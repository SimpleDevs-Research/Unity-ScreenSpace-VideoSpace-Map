using System.Collections;
using System.Collections.Generic;
using UnityEngine;
# if UNITY_EDITOR
using UnityEditor;
# endif

public class Calibration : MonoBehaviour
{
    [Header("=== Refs ===")]
    public Camera left_eye_ref;
    public Camera center_eye_ref;
    public Camera right_eye_ref;
    public Transform gaze_target_prefab;

    [Header("=== Results Writing ===")]
    public CSVWriter writer;
    public float time_between_targets = 5f;
    private bool _is_active = false;

    [Header("=== Target Placement ===")]
    [Range(0f, 90f)] public float theta_degrees;
    [Range(0f, 1f)] public float phi_ratio;
    public float phi_degrees => phi_ratio * 360f;
    public float radius;

    [Header("=== Cache ===")]
    public List<Transform> targets = new List<Transform>();
    
    # if UNITY_EDITOR
    void OnDrawGizmos() {
        if (Application.isPlaying) return;
        if (center_eye_ref == null) return;
        Vector3 v = center_eye_ref.transform.rotation * CalculateLocalVector(theta_degrees, phi_degrees, radius);
        Gizmos.color = Color.yellow;
        Gizmos.DrawLine(center_eye_ref.transform.position, center_eye_ref.transform.position + v);
        Gizmos.color = Color.grey;
        Gizmos.DrawSphere(center_eye_ref.transform.position + v, 0.15f);
    }
    # endif

    public static Vector3 CalculateLocalVector(float t, float p, float r) {
        float theta_rad = Mathf.Deg2Rad * t;
        float phi_rad = Mathf.Deg2Rad * p;

        // calculate spherical coordinates in local space
        float x = Mathf.Sin(theta_rad) * Mathf.Cos(phi_rad);
        float y = Mathf.Sin(theta_rad) * Mathf.Sin(phi_rad);
        float z = Mathf.Cos(theta_rad);

        Vector3 local_dir = Vector3.Normalize(new Vector3(x, y, z)) * r;
        return local_dir;
    }

    public void CreateNewTarget() {
        if (center_eye_ref == null) {
            Debug.LogError("Cannot instantiate new target if reference to the user's head is missing.");
            return;
        }

        // Calculate relative position
        Vector3 v = center_eye_ref.transform.rotation * CalculateLocalVector(theta_degrees, phi_degrees, radius);

        // Instantiate
        Transform t = Instantiate(gaze_target_prefab, center_eye_ref.transform.position + v, Quaternion.LookRotation(-v)) as Transform;
        CalibrationTarget ct = t.GetComponent<CalibrationTarget>();
        if (ct != null) ct.init_rotation = Quaternion.LookRotation(-v);
        t.SetParent(center_eye_ref.transform);

        // Add to list of instantiated targets
        targets.Add(t);
    }

    public void RemoveTarget(Transform t) {
        targets.Remove(t);
        DestroyImmediate(t.gameObject);
    }

    void Start() {
        for(int i = 0; i < targets.Count; i++) {
            CalibrationTarget ct = targets[i].GetComponent<CalibrationTarget>();
            if (ct != null) ct.SetNumber(i);
        }
    }

    public void RunCalibration() {
        // End prematurely if we are already running a calibration cycle
        if (_is_active) {
            Debug.Log("Already running a coroutine event!");
            return;
        }

        // Disable the ability to run another calibration
        _is_active = true;

        // Initialize calibration run
        StartCoroutine(CalibrationRun());
    }

    public IEnumerator CalibrationRun() {
        // Initialize event writer
        writer.Initialize();

        // Hide all calibration targets
        foreach(Transform t in targets) t.gameObject.SetActive(false);

        // Writer first line
        float start_frame = FrameCount.Instance.frame_count;
        float start_time = Time.time;
        writer.AddPayload(start_frame);   // frame #
        writer.AddPayload(start_time);    // timestamp
        writer.AddPayload("Start");       // event
        writer.AddPayload("");            // target_number
        writer.AddPayload(Vector3.zero);  // world position
        writer.AddPayload(Vector3.zero);  // screen left pos
        writer.AddPayload(Vector3.zero);  // screen center pos
        writer.AddPayload(Vector3.zero);  // screen right pos
        writer.WriteLine();

        // Run Through Loop
        WaitForSeconds wait_event = new WaitForSeconds(time_between_targets);
        for(int i = 0; i < targets.Count; i++) {
            // Make this transform visible
            Transform t = targets[i];
            t.gameObject.SetActive(true);

            // Get screen positions
            Vector3 left_screen_pos = left_eye_ref.WorldToScreenPoint(t.position);
            Vector3 center_screen_pos = center_eye_ref.WorldToScreenPoint(t.position);
            Vector3 right_screen_pos = right_eye_ref.WorldToScreenPoint(t.position);

            // Write to event
            writer.AddPayload(FrameCount.Instance.frame_count); // frame #
            writer.AddPayload(Time.time - start_time);    // timestamp
            writer.AddPayload("Target");             // event
            writer.AddPayload(i);                    // target number
            writer.AddPayload(t.position);          // world_pos
            writer.AddPayload(left_screen_pos);     // screen_left_pos
            writer.AddPayload(center_screen_pos);   // screen_center_pos
            writer.AddPayload(right_screen_pos);    // screen_right_pos
            writer.WriteLine();

            // Wait, then make invisible
            yield return wait_event;
            t.gameObject.SetActive(false);
        }

        // Write final line
        writer.AddPayload(FrameCount.Instance.frame_count); // frame #
        writer.AddPayload(Time.time - start_time);    // timestamp
        writer.AddPayload("End");         // event
        writer.AddPayload("");            // target_number
        writer.AddPayload(Vector3.zero);  // world position
        writer.AddPayload(Vector3.zero);  // screen left pos
        writer.AddPayload(Vector3.zero);  // screen center pos
        writer.AddPayload(Vector3.zero);  // screen right pos
        writer.WriteLine();

        // Terminate event writer
        writer.Disable();

        // Re-enable all calibration targets
        foreach(Transform t in targets) t.gameObject.SetActive(true);

        // Re-enable ability to run through coroutine
        _is_active = false;
    }

    public void ToggleTargets() {
        for(int i = 0; i < targets.Count; i++) {
            GameObject target = targets[i].gameObject;
            target.SetActive(!target.activeInHierarchy);
        }
    }
}
