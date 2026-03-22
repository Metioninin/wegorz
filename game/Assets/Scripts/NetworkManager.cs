using System;
using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;

/*[Serializable] public class Request
{
    public int ith;
    public bool force;
    public Request()
    { }
    public Request(bool force, int ith)
    {
        this.force = force;
        this.ith = ith;
    }
}

[Serializable] public class TasiemiecResponse
{
    public Notation tasiemiec;
}

[Serializable] public class LobbyResponse
{
    public Lobby lobby;
}*/

public class NetworkManager : MonoBehaviour
{
    /*string WEB_URL = "htttps://google.com";
    string SECRET = "uihabsdguvasd324132414";
    public float refreshRate = 5;
    bool currForce = false;
    [SerializeField] Interpreter interpreter;
    [SerializeField] Ranking lobbyScene;
    [SerializeField] Toggle forceToggle;

    IEnumerator SendRequest(bool force)
    {
        Request data = new Request(force, PlayerPrefs.GetInt("currentGame"));
        string json = JsonUtility.ToJson(data);
        using (UnityWebRequest request = new UnityWebRequest(WEB_URL, "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();

            request.SetRequestHeader("Content-Type", "application/json");
            request.SetRequestHeader("Authorization", "Bearer " + SECRET);

            yield return request.SendWebRequest();

            if (request.result != UnityWebRequest.Result.Success)
                Debug.LogError("B³¹d sieci: " + request.error);
            else
            {
                HandleResponse(request.downloadHandler.text);
            }
        }
    }

    void HandleResponse(string message)
    {
        if(message.Contains("tasiemiec"))
        {
            interpreter.StartGame(JsonUtility.FromJson<TasiemiecResponse>(message).tasiemiec);
        }
        else
        {
            lobbyScene.SetWaitingList(JsonUtility.FromJson<LobbyResponse>(message).lobby);
        }
    }

    IEnumerator SlowerUpdate()
    {
        while(true)
        {
            if(!interpreter.IsGamePlaying())
                StartCoroutine(SendRequest(currForce));
            yield return new WaitForSeconds(refreshRate);
        }
    }

    private void Start()
    {
        if (!PlayerPrefs.HasKey("currentGame"))
            PlayerPrefs.SetInt("currentGame", 1);
        StartCoroutine(SlowerUpdate());
    }

    public void ResetGameNumber()
    {
        PlayerPrefs.SetInt("currentGame", 1);
    }

    public void ToggleFastStart()
    {
        currForce = forceToggle.isOn;
    }

    public void ResetToggle()
    {
        forceToggle.isOn = currForce = false;
    }*/
}
