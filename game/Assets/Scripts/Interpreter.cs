using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using TMPro;
using UnityEngine;

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
    public Moves(List<pair> moves)
    {
        this.moves = moves;
    }   
}

[Serializable]public class Order
{
    public string name;
    public float points;
    public Order()
    {}
    public Order(string name, float points)
    {
        this.name = name;
        this.points = points;
    }
}

//przy zmianie stosunku bokow nalezy zmienic rozdzielczosc gry i dostosowac zmienna k_unity i zmienic n i m
[Serializable] public class Notation
{
    public int k; // k = n / sta, k = m / stb
    public List<Order> playerNames; //w kolejnosci rankingu
    public List<Moves> framesTop;
    public List<Moves> framesBottom;
    public List<int> zone;
    public List<Order> ranking;
    public Notation(){}

    /*public static Notation Read(FileInfo file)
    {
        string path = file.FullName;
        return JsonUtility.FromJson<Notation>(File.ReadAllText(path));
    }*/
}

[Serializable] public class Lobby
{
    public int currentPlayers;
    public int desiredPlayers;
    public Lobby() { }
    public Lobby(int currentPlayers, int desiredPlayers)
    {
        this.currentPlayers = currentPlayers;
        this.desiredPlayers = desiredPlayers;
    }
}

public class Interpreter : MonoBehaviour
{
    public GameObject playerObject;
    List<GameObject> players = new List<GameObject>(), grid = new List<GameObject>();
    int playerCount, currentFrame = 1;
    public float refreshRate = 1;
    float speed = 1;
    public float speed2 = 1;
    bool isGameStarted = false;
    public int k_Unity; //dlugosc boku mapy(krotsza) / st_a
    public float n = 10, m = 15;
    [SerializeField] GameObject winnerArea, gridObject;
    public float gridThickness;
    [SerializeField] TextMeshProUGUI winnerText;
    [SerializeField] Ranking ranking;
    [SerializeField] Transform[] zoneMasks; //LRUD
    [SerializeField] TextMeshProUGUI speedLabel;
    List<Anim> animations = new List<Anim>();
    Notation data;
    [SerializeField] AudioSource src;
    [SerializeField] NetworkManager networkManager;

    [SerializeField] AudioClip popSfx, winSfx, startGameSfx;

    private void Start()
    {
        /*Notation test = new Notation();
        int _k = 3;
        List<string> _playerNames = new List<string> { "A", "B", "C" };
        List<Moves> _framesTop = new List<Moves> {new Moves(new List<pair> {new pair(0, 6), new pair(4, 6), new pair(6, 1)}),
        new Moves(new List<pair> {new pair(1, 6), new pair(3, 6), new pair(6, 2)}), 
        new Moves(new List<pair> {new pair(2, 6), new pair(-1, -1), new pair(6, 3)}),
        new Moves(new List<pair> {new pair(2, 5), new pair(-1, -1), new pair(5, 3)})};
        
        List<Moves> _framesBottom = new List<Moves> {new Moves(new List<pair> {new pair(1, 5), new pair(5, 5), new pair(7, 0)}),
        new Moves(new List<pair> {new pair(2, 5), new pair(4, 5), new pair(7, 1)}),
        new Moves(new List<pair> {new pair(4, 4), new pair(-1, -1), new pair(7, 2)}),
        new Moves(new List<pair> {new pair(4, 3), new pair(-1, -1), new pair(6, 2)})};
        List<int> _zone = new List<int> { 0, 0, 0, 1, 1, 1, 1 };

        test.playerNames = _playerNames;
        test.zone = _zone;
        test.k = _k;
        test.framesBottom = _framesBottom;
        test.framesTop = _framesTop;

        string json = JsonUtility.ToJson(test, true);
        File.WriteAllText(Application.persistentDataPath + "/pliczek.json", json);
        Debug.Log(Application.persistentDataPath);*/

        speed = speed2 / 1000f;
        speedLabel.text = speed2.ToString();
        //StartCoroutine(SlowerUpdate());
    }

    /*IEnumerator SlowerUpdate()
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
    }*/

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
                zoneMasks[i].localScale = new Vector2(size, n);
            for (int i = 2; i < 4; i++)
                zoneMasks[i].localScale = new Vector2(m, size);
        }
        else
        {
            for (int i = 0; i < 2; i++)
                animations.Add(new Anim(zoneMasks[i], zoneMasks[i].localScale, new Vector3(size, n, 1), 0, speed, true));
            for (int i = 2; i < 4; i++)
                animations.Add(new Anim(zoneMasks[i], zoneMasks[i].localScale, new Vector3(m, size, 1), 0, speed, true));
        }

        for (int i = 0; i < 2; i++)
            zoneMasks[i].localScale = new Vector2(zoneMasks[i].localScale.x, n - 2 * zoneMasks[i].localScale.x);
    }

    private void Update()
    {
        if (!isGameStarted) return;
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

        for(int i = 0; i < 2; i++)
            zoneMasks[i].localScale = new Vector2(zoneMasks[i].localScale.x, n - 2 * zoneMasks[i].localScale.x);
        
    }

    void NextFrame()
    {
        bool didDie = false;
        for (int j = 0; j < playerCount; j++)
        {
            if (!players[j].activeInHierarchy) continue;
            if (data.framesTop[currentFrame].moves[j].x == -1)
            {
                didDie = true;
                players[j].SetActive(false);
            }
            else
            {
                animations.Add(new Anim(players[j].transform, players[j].transform.position, WorldPos((data.framesTop[currentFrame].moves[j] + data.framesBottom[currentFrame].moves[j]) / 2), 0, speed, false));
                float wielBoku = data.framesBottom[currentFrame].moves[j].x - data.framesTop[currentFrame].moves[j].x;
                animations.Add(new Anim(players[j].transform, players[j].transform.localScale, new Vector3(kratka * wielBoku, kratka * wielBoku, 0), 0, 2f * speed, true));
            }
        }
        SetZone(data.zone[currentFrame] * kratka, false);
        if(didDie) src.PlayOneShot(popSfx);
        currentFrame++;
    }

    public void StartGame(Notation _data)
    {
        src.PlayOneShot(startGameSfx);
        data = _data;
        ranking.gameObject.SetActive(false);
        isGameStarted = true;
        foreach (var player in players) { Destroy(player); }
        players = new List<GameObject>();
        playerCount = data.playerNames.Count;
        kratka = (float)k_Unity / data.k;
        animations = new List<Anim>();
        currentFrame = 1;

        GenerateGrid();
        zoneMasks[0].localScale = zoneMasks[1].localScale = new Vector2(0, n); //lr
        zoneMasks[2].localScale = zoneMasks[3].localScale = new Vector2(m, 0); //du
        for (int i = 0; i < playerCount; i++)
        {
            GameObject newPlayer = Instantiate(playerObject, WorldPos((data.framesTop[0].moves[i] + data.framesBottom[0].moves[i]) / 2), Quaternion.identity);
            System.Random random = new System.Random();
            Color color = new Color((float)random.Next(0, 255) / 255, (float)random.Next(0, 255) / 255, (float)random.Next(0, 255) / 255, 1);
            newPlayer.GetComponent<Player>().SetPlayer(data.playerNames[i].name, color);
            newPlayer.transform.localScale = new Vector2(kratka, kratka);
            players.Add(newPlayer);
        }
        SetZone(data.zone[0] * kratka, true);
        NextFrame();
    }

    IEnumerator EndGame()
    {
        yield return new WaitForSeconds(1 / speed2);

        src.PlayOneShot(winSfx);
        winnerArea.SetActive(true);
        winnerText.text = data.playerNames[0].name;
        winnerArea.GetComponent<Ranking>().SetRanking(data.playerNames);
        yield return new WaitForSeconds(5 / speed2);
        winnerArea.SetActive(false);

        PlayerPrefs.SetInt("currentGame", PlayerPrefs.GetInt("currentGame") + 1);
        ranking.gameObject.SetActive(true);
        ranking.SetRanking(data.ranking);
        networkManager.ResetToggle();
        isGameStarted = false;
    }

    void GenerateGrid()
    {
        foreach (var item in grid)
            Destroy(item);
        grid.Clear();
        float x = WorldPos(new pair(1, 0)).x;
        while(x < m / 2)
        {
            var obj = Instantiate(gridObject, new Vector2(x, 0), Quaternion.identity);
            obj.transform.localScale = new Vector2(kratka * gridThickness, n);
            grid.Add(obj);
            x += kratka;
        }
        float y = WorldPos(new pair(0, 1)).y;
        while(y < n / 2)
        {
            var obj = Instantiate(gridObject, new Vector2(0, y), Quaternion.identity);
            obj.transform.localScale = new Vector2(m, kratka * gridThickness);
            grid.Add(obj);
            y += kratka;
        }
    }

    public void MoreSpeed()
    {
        speed2 += .5f;
        speedLabel.text = speed2.ToString();
        speed = speed2 / 1000f;
    }

    public void LessSpeed()
    {
        speed2 -= .5f;
        speedLabel.text = speed2.ToString();
        speed = speed2 / 1000f;
    }

    public bool IsGamePlaying()
    {
        return isGameStarted;
    }
}