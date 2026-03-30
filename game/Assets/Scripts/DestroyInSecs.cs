using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class DestroyInSecs : MonoBehaviour
{
    public float secs;
    void Dest()
    {
        Destroy(gameObject);
    }

    private void Start()
    {
        GetComponent<Animator>().SetTrigger("go");
        Invoke("Dest", secs);
    }
}
