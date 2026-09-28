"""Lightweight memory relevance; background tasks must not dominate small talk."""
import re

STOPWORDS=set('a an the i me my you your we our they their it its this that these those '
    'is are am was were be been being do does did have has had to of for from in on at '
    'and or but so just really very can could would should what how why when where who '
    'with about up not no yes hey hi hello yo man please tell know'.split())


def words(text):
    return set(re.findall(r"[a-z]+",text.lower()))-STOPWORDS


def asks_for_task(text):
    if declines_task(text):return False
    return bool(re.search(r'\b(?:any|some) (?:work|jobs?|errands?|tasks?)\b|'
        r'\b(?:do you|you) (?:need|want) (?:any |some )?help\b|\bcan i help\b|'
        r'\bwhat (?:should|can) i do\b|\b(?:quest|mission|errand|delivery|parcel|package)\b',text,re.I))


def declines_task(text):
    return bool(re.search(r"\b(?:forget|stop|drop|enough)\b.{0,40}\b(?:work|missions?|quests?|tasks?|letters?|delivery|jobs?)\b|\bno (?:more )?(?:work|jobs?|errands?|missions?|quests?|tasks?|deliveries)\b|\b(?:just|only) (?:want to )?(?:chat|talk)\b|\b(?:change the subject|something else)\b",text,re.I))


def relevant_rows(rows,query):
    wanted=words(query)
    ranked=[]
    for row in rows:
        overlap=len(wanted & words(row['key'].replace('_',' ')+' '+row['value']))
        # The old game used this key before memory topics existed. Preserve data
        # while applying the same relevance rule to those existing saves.
        task=row.get('topic')=='task' or row['key']=='current delivery'
        episodic=row['key'].startswith('event ')
        task_overlap=overlap
        if task:
            if declines_task(query):continue
            # Mentioning an NPC's name ("do you like Elena?") is not itself an
            # invitation to bring up every errand involving that NPC.
            names={name.lower() for name in re.findall(r'\b[A-Z][a-z]+\b',row['value'])}
            task_overlap=len(wanted & (words(row['key']+' '+row['value'])-names))
            if not asks_for_task(query) and not re.search(r'\b(?:who|where|when|which|whose|deliver|carry|take|bring|give|finish|complete)\b',query,re.I):
                task_overlap=0
            if re.search(r'\b(?:forget|stop|drop|enough)\b.{0,30}\b(?:work|mission|quest|task|letter|delivery|job)\b',query,re.I):
                continue
            if re.search(r'\bno (?:more )?(?:errands?|missions?|quests?|tasks?|deliveries)\b',query,re.I):
                continue
        if query and (task or episodic) and not (task_overlap if task else overlap) and not (task and asks_for_task(query)):
            continue
        ranked.append((overlap,row))
    ranked.sort(key=lambda pair:(-pair[0],-pair[1]['importance'],-pair[1]['updated']))
    return [row for _,row in ranked]
