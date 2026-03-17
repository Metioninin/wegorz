using System.Collections;
using System.Collections.Generic;
using Unity.VisualScripting;
using UnityEngine;

public class Shadow : MonoBehaviour
{
    [SerializeField] Vector3 offset;
    private void Start()
    {
        var o = Instantiate(this, transform.position, Quaternion.identity);
        for(int i = 0; i < o.transform.childCount; i++)
            Destroy(o.transform.GetChild(i).gameObject);
        foreach(Component comp in o.GetComponents<Component>())
            if (!(comp is SpriteRenderer) && !(comp is Transform))
                Destroy(comp);
        o.transform.SetParent(transform, false);
        o.transform.localPosition = offset;
        o.transform.localScale = Vector3.one;
        o.GetComponent<SpriteRenderer>().color = new Color(0.27f, 0.27f, 0.27f, 0.2f);
        o.GetComponent<SpriteRenderer>().sortingOrder = GetComponent<SpriteRenderer>().sortingOrder - 1;
    }
}
