using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class Card : MonoBehaviour
{
    public Sprite[] colorIcons;
    public SpriteRenderer background;
    public TextMeshProUGUI[] numbers;
    public Animator animator;
    public void SetColor(CardInfo cardInfo)
    {
        foreach (var item in numbers) item.text = cardInfo.numer;
        background.sprite = colorIcons[cardInfo.kolor];
        animator.SetTrigger("go");
        SoundManager.Instance.PlaySfx(SoundManager.Instance.card[Random.Range(0, SoundManager.Instance.card.Length)]);
    }
}
