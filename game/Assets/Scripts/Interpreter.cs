using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using TMPro;
using Unity.VisualScripting;
using UnityEditor.U2D;
using UnityEngine;
using UnityEngine.XR;

public class Anim
{
    public Transform obj;
    public Vector3 startPos, endPos;
    public float progress, speed;
    public bool scale;
    public Anim() { }
    public Anim(Transform obj, Vector3 startPos, Vector3 endPos, float progress, float speed, bool scale)
    {
        this.obj = obj;
        this.startPos = startPos;
        this.endPos = endPos;
        this.progress = progress;
        this.speed = speed;
        this.scale = scale;
    }
}

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
    public List<string> playerNames; //w kolejnosci rankingu
    public List<Moves> framesTop;
    public List<Moves> framesBottom;
    public string winner;
    public List<int> zone;
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
    int playerCount, currentFrame = 1;
    public float refreshRate = 1;
    public float speed = 1;
    bool isGameStarted = false, isGameEnded = false;
    public int k_Unity; //dlugosc boku mapy(krotsza) / st_a
    public float n = 10, m = 15;
    [SerializeField] GameObject winnerArea;
    [SerializeField] TextMeshProUGUI winnerText;
    [SerializeField] Ranking ranking;
    [SerializeField] Transform[] zoneMasks; //LRUD
    [SerializeField] TextMeshProUGUI speedLabel;
    List<Anim> animations = new List<Anim>();
    Notation data;

    private void Start()
    {
        speedLabel.text = speed.ToString();
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

            StartGame(newData);
        }
    }

    float kratka;
    Vector2 WorldPos(pair pos)
    {
        pair p = new pair(pos.x * kratka, pos.y * kratka);
        return new Vector2(p.x - m / 2, p.y - n / 2);
    }

    void SetZone(float size, bool init)
    {
        if (init)
        {
            for (int i = 0; i < 2; i++)
                zoneMasks[i].localScale = new Vector2(size, 1);
            for (int i = 2; i < 4; i++)
                zoneMasks[i].localScale = new Vector2(1, size);
        }
        else
        {
            for (int i = 0; i < 2; i++)
                animations.Add(new Anim(zoneMasks[i], zoneMasks[i].localScale, new Vector3(size, 1, 1), 0, speed, true));
            for (int i = 2; i < 4; i++)
                animations.Add(new Anim(zoneMasks[i], zoneMasks[i].localScale, new Vector3(1, size, 1), 0, speed, true));
        }
    }

    private void Update()
    {
        if (animations.Count == 0) return;
        bool going = false;
        foreach (var anim in animations)
            if (anim.progress < 1)
                going = true;
        if(!going)
        {
            animations.Clear();
            if(currentFrame == data.framesBottom.Count)
            {
                StartCoroutine(EndGame());
                return;
            }
            NextFrame();
        }


        foreach(var item in animations)
        {
            if (item.scale)
                item.obj.localScale = Vector3.Lerp(item.startPos, item.endPos, item.progress);
            else
                item.obj.position = Vector3.Lerp(item.startPos, item.endPos, item.progress);
            item.progress += item.speed;
        }
    }

    void NextFrame()
    {
        for (int j = 0; j < playerCount; j++)
        {
            if (!players[j].activeInHierarchy) continue;
            if (data.framesTop[currentFrame].moves[j] == new pair(-1, -1)) players[j].SetActive(false);
            else
            {
                animations.Add(new Anim(players[j].transform, players[j].transform.position, WorldPos((data.framesTop[currentFrame].moves[j] + data.framesBottom[currentFrame].moves[j]) / 2), 0, speed, false));
                float wielBoku = data.framesBottom[currentFrame].moves[j].x - data.framesTop[currentFrame].moves[j].x;
                animations.Add(new Anim(players[j].transform, players[j].transform.localScale, new Vector2(kratka * wielBoku, kratka * wielBoku), 0, 2f * speed, true));
            }
        }
        SetZone(data.zone[currentFrame] * kratka, false);

        currentFrame++;
    }

    void StartGame(Notation _data)
    {
        data = _data;
        ranking.gameObject.SetActive(false);
        isGameStarted = true;
        players = new List<GameObject>();
        playerCount = data.playerNames.Count;
        kratka = k_Unity / data.k;

        zoneMasks[0].GetChild(0).localPosition = new Vector2(kratka / 2, 0); //l
        zoneMasks[1].GetChild(0).localPosition = new Vector2(-kratka / 2, 0); //r
        zoneMasks[2].GetChild(0).localPosition = new Vector2(0, -kratka / 2); //u
        zoneMasks[3].GetChild(0).localPosition = new Vector2(0, kratka / 2); //d

        zoneMasks[0].GetChild(0).localScale = zoneMasks[1].localScale = new Vector2(0, 1); //lr
        zoneMasks[2].GetChild(0).localScale = zoneMasks[3].localScale = new Vector2(1, 0); //du

        for (int i = 0; i < playerCount; i++)
        {
            GameObject newPlayer = Instantiate(playerObject, WorldPos((data.framesTop[0].moves[i] + data.framesBottom[0].moves[i]) / 2), Quaternion.identity);
            newPlayer.GetComponent<Player>().SetPlayer(data.playerNames[i], new Color(UnityEngine.Random.Range(0, 255), UnityEngine.Random.Range(0, 255), UnityEngine.Random.Range(0, 255)));
            newPlayer.transform.localScale = new Vector2(kratka, kratka);
            players.Add(newPlayer);
            SetZone(data.zone[i] * kratka, true);
        }
        NextFrame();
    }

    IEnumerator EndGame()
    {
        winnerArea.SetActive(true);
        winnerText.text = data.winner;
        yield return new WaitForSeconds(15f / speed);
        winnerArea.SetActive(false);

        ranking.gameObject.SetActive(true);
        ranking.SetRanking(data.playerNames);
        isGameStarted = false;
    }

    public void MoreSpeed()
    {
        speed += .5f;
        speedLabel.text = speed.ToString();
    }

    public void LessSpeed()
    {
        speed -= .5f;
        speedLabel.text = speed.ToString();
    }
}