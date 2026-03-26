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
    public GameManager gameManager;
    public float refreshRate = 1;
    bool isGameStarted = false;
    Tasiemiec dataLong;
    int currentGame = 0;
    public int gamesInOne = 3;

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
        if (currentGame >= dataLong.data.Count || dataLong == null) return;
        List<Notation> nextGames = new List<Notation>();
        for (int i = 0; i < gamesInOne; i++)
            nextGames.Add(dataLong.data[currentGame++]);
        gameManager.StartGames(nextGames);
    }
}