using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using TMPro;
using UnityEngine;

[Serializable]
public class Notation
{
    public string name1, name2;
    public int move1, move2, gain1, gain2;
    public List<Order> ranking;
}

public class Game : MonoBehaviour
{
    public AudioClip mixSFX, greetSFX, fightSFX;
    public AudioSource src;
    public Vector2[] pos;
    public GameObject gameArea, rankingArea, greet, fight;
    public TextMeshProUGUI player1, player2;
    public Animator[] gainAnim;
    List<Animator> iconAnim = new List<Animator>();
    public Sprite[] icons;
    public Ranking ranking;
    public IEnumerator StartGame(Notation data)
    {
        rankingArea.SetActive(false);
        gameArea.SetActive(true);

        if(data.move1 == 0) iconAnim.Add(Instantiate(greet, pos[0], Quaternion.identity, gameArea.transform).transform.GetChild(0).GetComponent<Animator>());
        else iconAnim.Add(Instantiate(fight, pos[0], Quaternion.identity, gameArea.transform).transform.GetChild(0).GetComponent<Animator>());
        if(data.move2 == 0) iconAnim.Add(Instantiate(greet, pos[1], Quaternion.identity, gameArea.transform).transform.GetChild(0).GetComponent<Animator>());
        else iconAnim.Add(Instantiate(fight, pos[1], Quaternion.identity, gameArea.transform).transform.GetChild(0).GetComponent<Animator>());

        for (int i = 0; i < 2; i++)
        {
            iconAnim[i].gameObject.SetActive(false);
            gainAnim[i].gameObject.SetActive(false);
        }
        player1.text = data.name1;
        player2.text = data.name2;

        yield return new WaitForSeconds(1);

        for (int i = 0; i < 2; i++)
            iconAnim[i].gameObject.SetActive(true);
        iconAnim[0].GetComponent<SpriteRenderer>().sprite = icons[data.move1];
        iconAnim[1].GetComponent<SpriteRenderer>().sprite = icons[data.move2];
        if (data.move1 != data.move2) src.PlayOneShot(mixSFX);
        else if (data.move1 == 0) src.PlayOneShot(greetSFX);
        else src.PlayOneShot(fightSFX);
        for (int i = 0; i < 2; i++) iconAnim[i].SetTrigger("start");

        yield return new WaitForSeconds(1);

        for (int i = 0; i < 2; i++)
            gainAnim[i].gameObject.SetActive(true);
        gainAnim[0].GetComponent<TextMeshProUGUI>().text = data.gain1.ToString();
        gainAnim[1].GetComponent<TextMeshProUGUI>().text = data.gain2.ToString();
        for (int i = 0; i < 2; i++) gainAnim[i].SetTrigger("start");

        yield return new WaitForSeconds(2);

        foreach (var item in iconAnim)
            Destroy(item.gameObject.transform.parent.gameObject);
        iconAnim = new List<Animator>();
        gameArea.SetActive(false);
        rankingArea.SetActive(true);
        ranking.ShowRanking(data.ranking);
    }
}
