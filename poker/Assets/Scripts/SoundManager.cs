using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class SoundManager : MonoBehaviour
{
    public AudioClip fold, bet, win, start, allin; 
    public AudioClip[] card;
    AudioSource src;
    public static SoundManager Instance { get; private set; }

    private void Awake()
    {
        Instance = this;
        src = GetComponent<AudioSource>();
    }

    public void PlaySfx(AudioClip clip)
    {
        src.PlayOneShot(clip);
    }
}
