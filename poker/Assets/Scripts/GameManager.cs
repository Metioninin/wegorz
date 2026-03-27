using System;
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEditor;
using UnityEngine;

[Serializable]
public class CardInfo
{
    public int kolor; //0->kier, 1->pik, 2->karo, 3->trefl
    public string numer;
}

[Serializable]
public class PlayerInfo
{
    public string name;
    public int money;
    public int bet;
    public List<CardInfo> cards;
}

[Serializable]
public class MoveInfo
{
    public int index;
    public int money;
    public int bet;
    public string move;
    public int pula;
}

[Serializable]
public class Frame
{
    public List<MoveInfo> moves;
    public List<CardInfo> mutualCards;
}
[Serializable]
public class Notation
{
    public List<PlayerInfo> players;
    public List<Frame> frames;
    public List<Order> ranking;
    public int winnerIndex;
}

public class GameManager : MonoBehaviour
{
    public float right = 5.5f, top = 3.5f;
    public GameObject player, card;
    List<GameObject> instPlayers = new List<GameObject>(), instCards = new List<GameObject>();
    public Transform cardHolder;
    public float distanceBetweenCards = .8f;
    Notation data;
    public float moveTime, frameTime;
    public Ranking ranking;
    public GameObject rankingArea, gameArea;
    public TextMeshProUGUI potText;
    public Transform potAnimation;
    public float potAnimationSpeed;
    public RectTransform canvas;
    int currentGame;
    List<Notation> games;
    public void StartGame()
    {
        SoundManager.Instance.PlaySfx(SoundManager.Instance.start);
        Notation data = games[currentGame];
        potText.text = (data.players.Count * 10).ToString() + "$"; //TUTAJ ZMIEN BLINDA
        rankingArea.SetActive(false);
        gameArea.SetActive(true);
        CreatePlayer(new Vector2(-right, 0), data.players[0]);
        CreatePlayer(new Vector2(right, 0), data.players[1]);
        for (int i = 2; i < 2 + (data.players.Count - 1) / 2; i++)
        {
            float dl = 2 * right / (1 + ((data.players.Count - 1) / 2));
            CreatePlayer(new Vector2((-right + dl * (i - 1)), -top / (right * right) * (-right + dl * (i - 1)) * (-right + dl * (i - 1)) + top), data.players[i]);
        }
        for (int i = 2 + (data.players.Count - 1) / 2; i < data.players.Count; i++)
        {
            float dl = 2 * right / (1 + ((data.players.Count - 2) / 2));
            CreatePlayer(new Vector2(-right + dl * (i - 1 - (data.players.Count - 1) / 2), top / (right * right) * (-right + dl * (i - 1 - (data.players.Count - 1) / 2)) * (-right + dl * (i - 1 - (data.players.Count - 1) / 2)) - top), data.players[i]);
        }

        this.data = data;
        StartCoroutine(NextFrame());
    }

    int currFrame = 0;
    int currentPot = 0;
    IEnumerator NextFrame()
    {
        if (currFrame >= data.frames.Count)
        {
            StartCoroutine(EndGame());
            yield break;
        }
        Frame frame = data.frames[currFrame];

        for (int i = instCards.Count; i < frame.mutualCards.Count; i++)
        {
            CreateMutualCard(frame.mutualCards[i]);
            yield return new WaitForSeconds(moveTime);
        }

        for (int i = 0; i < frame.moves.Count; i++)
        {
            instPlayers[frame.moves[i].index].GetComponent<Player>().Highlight(true, false);
            instPlayers[frame.moves[i].index].GetComponent<Player>().UpdateInfo(frame.moves[i]);
            currentPot = frame.moves[i].pula;
            potText.text = currentPot.ToString() + "$";
            yield return new WaitForSeconds(moveTime);
            instPlayers[frame.moves[i].index].GetComponent<Player>().Highlight(false, false);
        }

        currFrame++;
        yield return new WaitForSeconds(frameTime);
        StartCoroutine(NextFrame());
    }

    void CreatePlayer(Vector2 pos, PlayerInfo info)
    {
        instPlayers.Add(Instantiate(player, pos, Quaternion.identity));
        instPlayers[instPlayers.Count - 1].GetComponent<Player>().SetInfo(info);
    }

    void CreateMutualCard(CardInfo info)
    {
        var newCard = Instantiate(card, cardHolder);
        newCard.transform.localPosition = new Vector2(distanceBetweenCards * instCards.Count, 0);
        newCard.GetComponent<Card>().SetColor(info);
        instCards.Add(newCard);
    }


    bool animationGoing = false;
    Vector2 startPos, endPos;
    float progress = 0;
    IEnumerator EndGame()
    {
        instPlayers[data.winnerIndex].GetComponent<Player>().Highlight(true, true);
        animationGoing = true;
        startPos = potAnimation.localPosition;
        endPos = instPlayers[data.winnerIndex].transform.position;
        Vector2 screenPoint = Camera.main.WorldToScreenPoint(instPlayers[data.winnerIndex].transform.position);
        RectTransformUtility.ScreenPointToLocalPointInRectangle(canvas, screenPoint, null, out endPos);
        yield return new WaitForSeconds(1 / potAnimationSpeed);
        SoundManager.Instance.PlaySfx(SoundManager.Instance.win);
        instPlayers[data.winnerIndex].GetComponent<Player>().money.text = (data.players[data.winnerIndex].money + currentPot).ToString() + "$";
        potAnimation.gameObject.SetActive(false);
        yield return new WaitForSeconds(1);

        potAnimation.gameObject.SetActive(true);
        progress = 0;
        animationGoing = false;
        foreach (var card in instCards)
            Destroy(card);
        foreach (var player in instPlayers)
            Destroy(player);
        currentPot = 0;
        currFrame = 1;
        instCards = new List<GameObject>();
        instPlayers = new List<GameObject>();
        currentGame++;

        if (currentGame == games.Count)
        {
            rankingArea.SetActive(true);
            gameArea.SetActive(false);
            ranking.ShowRanking(data.ranking);
        }
        else
        {
            StartGame();
        }
    }

    public void StartGames(List<Notation> gamess)
    {
        currentGame = 0;
        games = gamess;
        StartGame();
    }

    private void Update()
    {
        if (!animationGoing) return;
        potAnimation.localPosition = Vector2.Lerp(startPos, endPos, progress);
        progress += potAnimationSpeed * Time.deltaTime;
    }
}
