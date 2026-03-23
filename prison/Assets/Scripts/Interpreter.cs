using JetBrains.Annotations;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using TMPro;
using UnityEngine;

[Serializable]
public class Tasiemiec
{
    public List<Notation> data;
    public static Tasiemiec Read(FileInfo file)
    {
        string path = file.FullName;
        return JsonUtility.FromJson<Tasiemiec>(File.ReadAllText(path));
    }
}

public class Interpreter : MonoBehaviour
{
    public Game gameManager;
    public float refreshRate = 1;
    bool isGameStarted = false;
    Tasiemiec dataLong;
    int currentGame = 0;
    [SerializeField] AudioSource src;
    [SerializeField] AudioClip popSfx, winSfx, startGameSfx;

    private void Start()
    {
        StartCoroutine(SlowerUpdate());
    }

    IEnumerator SlowerUpdate()
    {
        while (true)
        {
            yield return new WaitForSeconds(refreshRate);
            if (isGameStarted) continue;
            DirectoryInfo dir = new DirectoryInfo(Application.persistentDataPath);
            FileInfo[] files = dir.GetFiles();

            if (files.Length == 0) continue;
            isGameStarted = true;
            FileInfo file = files[0];
            DateTime time = files[0].CreationTime;
            foreach (var item in files)
            {
                if (item.CreationTime < time)
                {
                    time = item.CreationTime;
                    file = item;
                }
            }

            dataLong = Tasiemiec.Read(file);
            Debug.Log("mam pliczek essa");
            break;
        }
    }

    public void StartGame()
    {
        if (currentGame == dataLong.data.Count || dataLong == null) return;
        StartCoroutine(gameManager.StartGame(dataLong.data[currentGame]));
        currentGame++;
    }
}