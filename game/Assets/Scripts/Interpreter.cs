using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using TMPro;
using UnityEngine;

[Serializable] public class pair
{
    public float x, y;
    public pair(float _x, float _y)
    {
        x = _x;
        y = _y;
    }
    public pair()
    {
        x = y = 0;
    }

    public static pair operator +(pair a, pair b)
    {
        return new pair(a.x + b.x, a.y + b.y);
    }
    public static pair operator /(pair a, int b)
    {
        return new pair(a.x / b, a.y / b);
    }
}

[Serializable] public class Moves
{
    public List<pair> moves;
    public Moves()
    {
        moves = new List<pair>();
    }
}

//przy zmianie stosunku bokow nalezy zmienic rozdzielczosc gry i dostosowac zmienna k_unity i zmienic n i m
[Serializable] public class Notation
{
    public int k; // k = n / sta, k = m / stb
    public List<string> playerNames;
    public List<Moves> framesTop;
    public List<Moves> framesBottom;
    public string winner;
    public Notation(){}

    public static Notation Read(FileInfo file)
    {
        string path = file.FullName;
        return JsonUtility.FromJson<Notation>(File.ReadAllText(path));
    }
}
public class Interpreter : MonoBehaviour
{
    public GameObject playerObject;
    List<GameObject> players;
    int playerCount;
    public float refreshRate = 1;
    public float speed = 1;
    bool isGameStarted = false;
    public int k_Unity; //dlugosc boku mapy(krotsza) / st_a
    public float n = 10, m = 15;
    [SerializeField] GameObject winnerArea;
    [SerializeField] TextMeshProUGUI winnerText;
    [SerializeField] Ranking ranking;

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

            Notation newData = Notation.Read(file);
            file.Delete();

            StartCoroutine(StartGame(newData));
        }
    }

    float kratka;
    Vector2 WorldPos(pair pos)
    {
        pair p = new pair(pos.x * kratka, pos.y * kratka);
        return new Vector2(p.x - m / 2, p.y - n / 2);
    }

    IEnumerator StartGame(Notation data)
    {
        isGameStarted = true;
        players = new List<GameObject>();
        playerCount = data.playerNames.Count;
        kratka = k_Unity / data.k;


        for (int i = 0; i < playerCount; i++)
        {
            GameObject newPlayer = Instantiate(playerObject, WorldPos((data.framesTop[0].moves[i] + data.framesBottom[0].moves[i]) / 2), Quaternion.identity);
            newPlayer.GetComponent<Player>().SetPlayer(data.playerNames[i], new Color(UnityEngine.Random.Range(0, 255), UnityEngine.Random.Range(0, 255), UnityEngine.Random.Range(0, 255)));
            newPlayer.transform.localScale = new Vector2(kratka, kratka);
            players.Add(newPlayer);
        }

        for (int i = 1; i < data.framesTop.Count; i++)
        {
            yield return new WaitForSeconds(1f / speed);
            for(int j = 0; j < playerCount; j++)
            {
                if (!players[j].activeInHierarchy) continue;
                if (data.framesTop[i].moves[j] == new pair(-1, -1)) players[j].SetActive(false);
                else
                {
                    players[j].transform.position = WorldPos((data.framesTop[i].moves[j] + data.framesBottom[i].moves[j]) / 2);
                    float wielBoku = data.framesBottom[i].moves[j].x - data.framesTop[i].moves[j].x;
                    players[j].transform.localScale = new Vector2(kratka * wielBoku, kratka * wielBoku);
                }
            }
        }

        winnerArea.SetActive(true);
        winnerText.text = data.winner;
        yield return new WaitForSeconds(15f / speed);
        winnerArea.SetActive(false);

        ranking.gameObject.SetActive(true);
        ranking.SetRanking();
    }
}