using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class Player : MonoBehaviour
{
    [SerializeField] TextMeshProUGUI nameLabel;
    [SerializeField] SpriteRenderer spriteRenderer;
    public void SetPlayer(string playerName, Color playerColor)
    {
        nameLabel.text = playerName;
        spriteRenderer.color = playerColor;
    }
}
