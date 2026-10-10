"""Small persistent per-NPC, per-player memory and reviewable dialogue records."""
import json
import hashlib
import re
import sqlite3
import threading
import time
from pathlib import Path
from .relevance import relevant_rows


class MemoryStore:
    def __init__(self, path, max_facts=128, max_turns=200):
        if max_facts<1 or max_turns<1:raise ValueError('Memory limits must be positive.')
        self.max_facts,self.max_turns=max_facts,max_turns
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;
            CREATE TABLE IF NOT EXISTS facts (
                npc TEXT, player TEXT, key TEXT, value TEXT, source TEXT,
                updated INTEGER DEFAULT (unixepoch()), PRIMARY KEY(npc,player,key));
            CREATE TABLE IF NOT EXISTS turns (
                id INTEGER PRIMARY KEY, npc TEXT, player TEXT, request TEXT,
                speech TEXT, seconds REAL, status TEXT DEFAULT 'unreviewed',
                edited TEXT, created INTEGER DEFAULT (unixepoch()));
            CREATE INDEX IF NOT EXISTS turn_owner ON turns(npc,player,id);
            CREATE TABLE IF NOT EXISTS relationships (
                npc TEXT, player TEXT, state TEXT, PRIMARY KEY(npc,player));
            CREATE TABLE IF NOT EXISTS character_context (
                npc TEXT, player TEXT, field TEXT, value TEXT, updated REAL,
                PRIMARY KEY(npc,player,field));
        ''')
        columns={row['name'] for row in self.db.execute('PRAGMA table_info(facts)')}
        with self.db:
            if 'importance' not in columns:
                self.db.execute('ALTER TABLE facts ADD COLUMN importance REAL DEFAULT 50')
            if 'expires' not in columns:
                self.db.execute('ALTER TABLE facts ADD COLUMN expires REAL')
            if 'topic' not in columns:
                self.db.execute("ALTER TABLE facts ADD COLUMN topic TEXT DEFAULT 'general'")

    def remember(self, npc, player, key, value, source="host", importance=50, ttl=None, topic='general'):
        if topic not in {'general','task'}:raise ValueError('Unknown memory topic.')
        if source not in {"host", "player_claim", "interaction", "suspicion"}:
            raise ValueError("Unknown memory source.")
        if not key.strip() or not value.strip():raise ValueError('Memory needs a key and text.')
        if not 0 <= importance <= 100:raise ValueError('Importance must be 0–100.')
        if ttl is not None and ttl <= 0:raise ValueError('Memory lifetime must be positive.')
        if source=='suspicion' and ttl is None:ttl=3600
        with self._lock, self.db:
            existing=self.db.execute('SELECT source FROM facts WHERE npc=? AND player=? AND key=?',(npc,player,key[:80])).fetchone()
            # An unverified claim must not replace a host-confirmed fact.
            if existing and existing['source']=='host' and source!='host':
                key='claim:'+key[:74]
            self.db.execute("INSERT OR REPLACE INTO facts(npc,player,key,value,source,importance,expires,topic) VALUES(?,?,?,?,?,?,?,?)",
                            (npc, player, key[:80], value[:240], source, importance, time.time()+ttl if ttl else None,topic))
            self.maintain(npc,player)

    def remember_event(self,npc,player,text,importance=60,ttl=86400,topic='general'):
        normalized=' '.join(text.casefold().split())
        key='event '+hashlib.sha256((topic+':'+normalized).encode()).hexdigest()[:24]
        self.remember(npc,player,key,text,'host',importance,ttl,topic)
        return key

    def update_character_context(self,npc,player,changes):
        """Host-owned state, separate from relationship numbers and player claims.

        Omitted fields persist. An empty value clears a field. No dialogue text
        can write these facts automatically or borrow another player's state.
        """
        allowed={'concern','intention','relationship','recent_event'}
        if not isinstance(changes,dict) or set(changes)-allowed:
            raise ValueError('Unknown character context field.')
        if any(not isinstance(v,str) or len(v)>240 for v in changes.values()):
            raise ValueError('Character context values must be text of at most 240 characters.')
        with self._lock,self.db:
            for key,value in changes.items():
                if value.strip():
                    self.db.execute('INSERT OR REPLACE INTO character_context VALUES(?,?,?,?,?)',
                                    (npc,player,key,value.strip(),time.time()))
                else:self.db.execute('DELETE FROM character_context WHERE npc=? AND player=? AND field=?',(npc,player,key))

    def character_context(self,npc,player):
        with self._lock:
            rows=self.db.execute('SELECT field,value,updated FROM character_context WHERE npc=? AND player=? ORDER BY field',(npc,player)).fetchall()
        return tuple(f"{r['field']}: {r['value']} (host; updated {r['updated']:.0f})" for r in rows)

    def facts(self,npc,player):
        with self._lock:
            rows=self.db.execute('SELECT * FROM facts WHERE npc=? AND player=? AND (expires IS NULL OR expires>?) ORDER BY importance DESC,updated DESC',
                                 (npc,player,time.time())).fetchall()
        return [dict(row) for row in rows]

    def forget(self,npc,player,key):
        with self._lock,self.db:
            self.db.execute('DELETE FROM facts WHERE npc=? AND player=? AND key=?',(npc,player,key))

    def prune_expired(self):
        with self._lock,self.db:
            return self.db.execute('DELETE FROM facts WHERE expires IS NOT NULL AND expires<=?',(time.time(),)).rowcount

    def learn_claims(self, npc, player, text):
        letter=r"[^\W\d_]"
        part=letter+r"(?:[^\W\d_]|['-](?=[^\W\d_])){0,29}"
        match=re.fullmatch(r"\s*(?:(?:hey|hi|hello)[,! ]+)?(?:(?:actually|no|sorry)[, ]+)?(?:my name is|my name's|(?:please )?call me)\s+("+part+r"(?:\s+"+part+r"){0,2})[.!]?\s*",text,re.I)
        if match:
            name=' '.join(match[1].split())
            if len(name)<=60 and name.split()[0].casefold() not in {'not','maybe','anything','whatever','me','later','back','when','tomorrow','a','an'}:
                self.remember(npc,player,'player_name',name,'player_claim',importance=80)

    def recall(self, npc, player, query="", limit=3):
        if limit<1:return ()
        rows=self.facts(npc,player)
        ranked = relevant_rows(rows,query)
        # A correction must survive unrelated high-overlap memories. Keep the
        # current canonical identity available without expanding the budget.
        identity=next((r for r in rows if r['key']=='player_name'),None)
        if identity:
            ranked=[identity]+[r for r in ranked if r['key']!='player_name']
        return tuple(f"{r['key'].replace('_',' ')}: {r['value']} ({r['source']})" for r in ranked[:limit])

    def history(self, npc, player, limit=12):
        with self._lock:
            rows = self.db.execute("SELECT request,COALESCE(edited,speech) AS speech FROM turns WHERE npc=? AND player=? AND status!='rejected' ORDER BY id DESC LIMIT ?",
                                   (npc, player, limit)).fetchall()
        return tuple((json.loads(r['request'])['player_text'], r['speech']) for r in reversed(rows))

    def record(self, npc, player, request, speech, seconds):
        with self._lock, self.db:
            cursor = self.db.execute("INSERT INTO turns(npc,player,request,speech,seconds) VALUES(?,?,?,?,?)",
                                     (npc, player, json.dumps(request, ensure_ascii=False), speech, seconds))
            self.maintain(npc,player)
            return cursor.lastrowid

    def maintain(self,npc,player):
        """Bound disposable memory per owner, retaining authored facts and reviewed examples."""
        with self._lock,self.db:
            expired=self.db.execute('DELETE FROM facts WHERE npc=? AND player=? AND expires IS NOT NULL AND expires<=?',(npc,player,time.time())).rowcount
            # Permanent host facts are authored world data, not disposable history.
            facts=self.db.execute("DELETE FROM facts WHERE rowid IN (SELECT rowid FROM facts WHERE npc=? AND player=? AND NOT(source='host' AND expires IS NULL) ORDER BY importance DESC,updated DESC,rowid DESC LIMIT -1 OFFSET ?)",
                                  (npc,player,self.max_facts)).rowcount
            turns=self.db.execute("DELETE FROM turns WHERE id IN (SELECT id FROM turns WHERE npc=? AND player=? AND status='unreviewed' ORDER BY id DESC LIMIT -1 OFFSET ?)",
                                  (npc,player,self.max_turns)).rowcount
        return dict(expired=expired,facts=facts,turns=turns)

    def review(self, ident, status, edited=None):
        if status not in {"accepted", "rejected", "unreviewed"}:
            raise ValueError("Unknown review status.")
        if edited is not None and not edited.strip():
            raise ValueError("An edited answer cannot be blank.")
        with self._lock, self.db:
            if self.db.execute("UPDATE turns SET status=?,edited=? WHERE id=?", (status, edited, ident)).rowcount != 1:
                raise ValueError("Example not found.")

    def examples(self, status=None):
        with self._lock:
            if status:
                rows = self.db.execute("SELECT * FROM turns WHERE status=? ORDER BY id", (status,)).fetchall()
            else:
                rows = self.db.execute("SELECT * FROM turns ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def export(self, path):
        rows = self.examples("accepted")
        with Path(path).open("w", encoding="utf-8") as output:
            for row in rows:
                output.write(json.dumps({"schema_version": 1, "source": "human_reviewed",
                    "request": json.loads(row['request']), "speech": row['edited'] or row['speech']}, ensure_ascii=False)+'\n')
        return len(rows)

    def close(self):
        with self._lock:
            self.db.close()

    def load_state(self, npc, player):
        with self._lock:
            row = self.db.execute('SELECT state FROM relationships WHERE npc=? AND player=?', (npc,player)).fetchone()
        return json.loads(row['state']) if row else None

    def save_state(self, npc, player, state):
        with self._lock, self.db:
            self.db.execute('INSERT OR REPLACE INTO relationships VALUES(?,?,?)', (npc,player,json.dumps(state)))
