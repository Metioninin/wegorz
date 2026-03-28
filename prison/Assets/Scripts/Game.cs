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

    public static Notation Read(FileInfo file)
    {
        string path = file.FullName;
        return JsonUtility.FromJson<Notation>(File.ReadAllText(path));
    }
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
    public GameObject error1, error2;

    private void Start()
    {
        ResetStats();
    }
    public IEnumerator StartGame(Notation data)
    {
        rankingArea.SetActive(false);
        gameArea.SetActive(true);

        if (data.move1 == 2 && data.move2 == 2)
        {
            error1.SetActive(true);
            error2.SetActive(true);
            UpdateStats("error", 2);
        }
        else if (data.move1 == 2)
        {
            error1.SetActive(true);
            UpdateStats("error", 1);
        }
        else if (data.move2 == 2)
        {
            error2.SetActive(true);
            UpdateStats("error", 1);
        }
        else
        {
            if (data.move1 == 0) iconAnim.Add(Instantiate(greet, pos[0], Quaternion.identity, gameArea.transform).transform.GetChild(0).GetComponent<Animator>());
            else iconAnim.Add(Instantiate(fight, pos[0], Quaternion.identity, gameArea.transform).transform.GetChild(0).GetComponent<Animator>());
            if (data.move2 == 0) iconAnim.Add(Instantiate(greet, pos[1], Quaternion.identity, gameArea.transform).transform.GetChild(0).GetComponent<Animator>());
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

            if (data.move1 == 0) UpdateStats("greet", data.gain1);
            else UpdateStats("fight", data.gain1);
            if (data.move2 == 0) UpdateStats("greet", data.gain2);
            else UpdateStats("fight", data.gain2);

            if (data.move1 != data.move2) UpdateStats("diff", 1);
            else if (data.move2 == data.move1 && data.move1 == 1) UpdateStats("2betray", 1);
            else UpdateStats("2greet", 1);
        }

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
        error2.SetActive(false);
        error1.SetActive(false);
        gameArea.SetActive(false);
        rankingArea.SetActive(true);
        ranking.ShowRanking(data.ranking);
    }

    void UpdateStats(string stat, int val)
    {
        if (!PlayerPrefs.HasKey(stat)) PlayerPrefs.SetInt(stat, val);
        else PlayerPrefs.SetInt(stat, PlayerPrefs.GetInt(stat) + val);
    }

    void ResetStats()
    {
        PlayerPrefs.DeleteAll();
    }
}
