using System.Collections;
using System.Collections.Generic;
using Unity.VisualScripting;
using UnityEngine;

public class CameraControl : MonoBehaviour
{
    public float zoomSpeed = .1f;
    public float grabSpeed = .1f;

    Camera me;

    private void Start()
    {
        me = GetComponent<Camera>();
    }
    private void Update()
    {
        float scroll = Input.GetAxis("Mouse ScrollWheel");
        me.orthographicSize = Mathf.Clamp(me.orthographicSize - zoomSpeed * scroll, .1f, 5);

        if (Input.GetMouseButton(0))
            transform.position = new Vector3(transform.position.x - Input.GetAxis("Mouse X") * grabSpeed, transform.position.y - Input.GetAxis("Mouse Y") * grabSpeed, -10); 
        if(Input.GetKeyDown(KeyCode.Escape))
        {
            transform.position = new Vector3(0, 0, -10);
            me.orthographicSize = 5;
        }    
    }
}
