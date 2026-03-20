using UnityEngine;

public class FitQuadToCamera : MonoBehaviour
{
    public Camera cam;
    public float distance = 5f;

    void LateUpdate()
    {
        float height = 2f * distance * Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
        float width = height * cam.aspect;

        transform.localPosition = new Vector3(0, 0, distance);
        transform.localScale = new Vector3(width, height, 1);
    }
}