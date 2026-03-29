using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;

public class Ranking : MonoBehaviour
{
    public float dist = 2f;
    public GameObject label;
    public Vector2 startPos;
    Vector2 currPos, startScrollingPos, endScrollingPos;
    public Transform mover;
    public float scrollingSpeed = 1;
    bool down = true;
    public float finalistsPercent = .1f;
    float progress = 0;
    public float waitTime = 0.5f;
    public float masksDistance;
    public int startIndex = 0;
    public TextMeshProUGUI waiting, desired;

    List<GameObject> ranking = new List<GameObject>();
    public void SetRanking(List<Order> names)
    {
        foreach(var item in ranking) 
            Destroy(item); 
        ranking.Clear();

        currPos = startPos;
        for (int i = startIndex; i < names.Count; i++)
        {
            var item = names[i];
            GameObject a = Instantiate(label);
            a.GetComponent<Label>().text.text = (i + 1).ToString() + ". " + item.name;
            a.GetComponent<Label>().points.text = item.points.ToString();
            if ((float)i / names.Count > finalistsPercent) a.GetComponent<Label>().badge.gameObject.SetActive(false);
            //else a.GetComponent<Label>().badge.sprite = a.GetComponent<Label>().badgeSprites[i];
            a.transform.SetParent(mover);
            a.transform.localPosition = currPos;
            currPos.y -= dist;
            ranking.Add(a);
        }

        startScrollingPos = Vector2.zero;
        endScrollingPos = new Vector2(0, Mathf.Max(0, Mathf.Abs(currPos.y - startPos.y) - masksDistance));
    }

    bool wait = false;
    float currWaitTime = 0;
    private void Update()
    {
        if(wait)
        {
            currWaitTime += Time.deltaTime;
            if(currWaitTime > waitTime)
            {
                currWaitTime = 0;
                wait = false;
            }
            if (wait) return;
        }
        mover.localPosition = Vector2.Lerp(startScrollingPos, endScrollingPos, progress);
        if (down) progress += scrollingSpeed;
        else progress -= scrollingSpeed;
        if (progress <= 0)
        {
            progress = 0;
            down = true;
            wait = true;
        }
        else if (progress >= 1)
        {
            progress = 1;
            down = false;
            wait = true;
        }
    }

    /*public void SetWaitingList(Lobby lobby)
    {
        waiting.text = "Oczekuje: " + lobby.currentPlayers.ToString();
        desired.text = "Potrzeba: " + lobby.desiredPlayers.ToString();
    }*/
}
