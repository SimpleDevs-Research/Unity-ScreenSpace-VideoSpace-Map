using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class WritePosition : MonoBehaviour
{
    public Camera center_eye_ref;
    public Camera left_eye_ref;
    public Camera right_eye_ref;
    public CSVWriter writer;

    // Start is called before the first frame update
    void Start() {
        if (AdditiveSceneManager.Instance != null)
        {
            GameObject e;
            if (AdditiveSceneManager.Instance.TryGetRef("center_eye", out e)) center_eye_ref = e.GetComponent<Camera>();
            if (AdditiveSceneManager.Instance.TryGetRef("left_eye", out e)) left_eye_ref = e.GetComponent<Camera>();
            if (AdditiveSceneManager.Instance.TryGetRef("right_eye", out e)) right_eye_ref = e.GetComponent<Camera>();
            if (center_eye_ref != null && left_eye_ref != null && right_eye_ref != null) {
                Debug.Log($"Position Writer for {gameObject.name} initialized!");
                writer.Initialize();   
            }
        }
    }

    void Update()
    {
        if (!writer.is_active) return;

        int frame = Time.frameCount;
        Vector3 world_pos = transform.position;
        Vector3 center_screen_pos = center_eye_ref.WorldToScreenPoint(world_pos);
        Vector3 left_screen_pos = left_eye_ref.WorldToScreenPoint(world_pos);
        Vector3 right_screen_pos = right_eye_ref.WorldToScreenPoint(world_pos);

        writer.AddPayload(frame);
        writer.AddPayload(world_pos);
        writer.AddPayload(center_screen_pos);
        writer.AddPayload(left_screen_pos);
        writer.AddPayload(right_screen_pos);
        writer.WriteLine();
    }

    void OnDestroy() {
        writer.Disable();
    }
}
