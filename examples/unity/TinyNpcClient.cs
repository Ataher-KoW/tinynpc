using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

// Pass a JSON body matching examples/scene.json. Start the local bridge first.
public class TinyNpcClient : MonoBehaviour
{
    [Serializable] private class Reply { public string speech; public string error; }

    public IEnumerator Talk(string requestJson, Action<string> onReply, Action<string> onError)
    {
        using (var request = new UnityWebRequest("http://127.0.0.1:8765/chat", "POST"))
        {
            request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(requestJson));
            request.downloadHandler = new DownloadHandlerBuffer();
            request.SetRequestHeader("Content-Type", "application/json");
            request.timeout = 60;
            yield return request.SendWebRequest();
            if (request.result != UnityWebRequest.Result.Success)
            {
                onError?.Invoke(request.error + " " + request.downloadHandler.text);
                yield break;
            }
            Reply reply;
            try { reply = JsonUtility.FromJson<Reply>(request.downloadHandler.text); }
            catch (Exception error) { onError?.Invoke(error.Message); yield break; }
            if (reply == null || string.IsNullOrWhiteSpace(reply.speech))
                onError?.Invoke("The local bridge returned no dialogue.");
            else onReply?.Invoke(reply.speech);
        }
    }
}
