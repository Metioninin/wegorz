using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class Player : MonoBehaviour
{
    public Transform cardHolder;
    public GameObject cardObject;
    public float distanceBetweenCards;
    public TextMeshProUGUI money, username, move;
    public GameObject highlight;
    public float animationDuration = .5f;
    public Image pfp;
    public Sprite[] pfpIcons;
    public Color winnerHighlightColor, normalHighlightColor;
    public void SetInfo(PlayerInfo info)
    {
        Material mat = move.fontMaterial;
        mat.EnableKeyword("OUTLINE_ON");
        mat.SetFloat("_OutlineWidth", 0.3f);
        mat.SetColor("_OutlineColor", new Color32(0, 0, 0, 255));
        move.UpdateMeshPadding();

        for (int i = 0; i < info.cards.Count; i++)
        {
            var card = Instantiate(cardObject, cardHolder);
            card.transform.localPosition = new Vector2(i * distanceBetweenCards, 0);
            card.GetComponent<Card>().SetColor(info.cards[i]);
        }
        money.text = info.money.ToString() + "$";
        username.text = info.name;
        System.Random random = new System.Random();
        pfp.sprite = pfpIcons[random.Next(0, pfpIcons.Length - 1)];
    }

    public void UpdateInfo(MoveInfo info)
    {
        money.text = info.money.ToString() + "$";
        if (info.move == "Raise" || info.move == "Bet")
            info.move += "\n" + info.bet.ToString() + "$";
        if (info.move != "Fold" && info.move != "Check" && info.move != "All In")
            SoundManager.Instance.PlaySfx(SoundManager.Instance.bet);
        else if (info.move == "All In")
            SoundManager.Instance.PlaySfx(SoundManager.Instance.allin);
        StartCoroutine(ShowTextAnimation(info.move));
        if (info.move == "Fold")
        {
            foreach (var card in GetComponentsInChildren<SpriteRenderer>())
                card.color = new Color(card.color.r, card.color.g, card.color.b, .2f);
            foreach (var card in GetComponentsInChildren<TextMeshProUGUI>())
                card.color = new Color(card.color.r, card.color.g, card.color.b, .2f);
            foreach (var card in GetComponentsInChildren<Image>())
                card.color = new Color(card.color.r, card.color.g, card.color.b, .2f);
            SoundManager.Instance.PlaySfx(SoundManager.Instance.fold);
        }
    }

    IEnumerator ShowTextAnimation(string text)
    {
        move.gameObject.SetActive(true);
        move.text = text;
        move.GetComponent<Animator>().SetTrigger("go");
        yield return new WaitForSeconds(animationDuration);
        move.gameObject.SetActive(false);
    }

    public void Highlight(bool val, bool winner)
    {
        if (winner) highlight.GetComponent<SpriteRenderer>().color = winnerHighlightColor;
        else highlight.GetComponent<SpriteRenderer>().color = normalHighlightColor;
        highlight.gameObject.SetActive(val);
        highlight.GetComponent<Animator>().SetTrigger("go");
    }
}
