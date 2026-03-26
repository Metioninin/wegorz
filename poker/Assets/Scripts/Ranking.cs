using System;
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;

[Serializable]
public class Order
{
    public string name;
    public float points;
}
public class Ranking : MonoBehaviour
{
    public float dist = 2f;
    public GameObject label;
    public Vector2 startPos;
    Vector2 currPos, startScrollingPos, endScrollingPos;
    public Transform mover;
    public float scrollingSpeed = 1;
    bool down = true;
    float progress = 0;
    public float waitTime = 0.5f;
    public float masksDistance;

    List<GameObject> ranking = new List<GameObject>();
    public void ShowRanking(List<Order> names)
    {
        foreach (var item in ranking)
            Destroy(item);
        ranking.Clear();

        currPos = startPos;
        for (int i = 0; i < names.Count; i++)
        {
            var item = names[i];
            GameObject a = Instantiate(label);
            a.GetComponent<Label>().text.text = (i + 1).ToString() + ". " + item.name;
            a.GetComponent<Label>().points.text = item.points.ToString() + "$";
            a.transform.SetParent(mover);
            a.transform.localPosition = currPos;
            currPos.y -= dist;
        }

        startScrollingPos = Vector2.zero;
        endScrollingPos = new Vector2(0, Mathf.Max(0, Mathf.Abs(currPos.y - startPos.y) - masksDistance));
    }

    bool wait = false;
    float currWaitTime = 0;
    private void Update()
    {
        if (wait)
        {
            currWaitTime += Time.deltaTime;
            if (currWaitTime > waitTime)
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
}
