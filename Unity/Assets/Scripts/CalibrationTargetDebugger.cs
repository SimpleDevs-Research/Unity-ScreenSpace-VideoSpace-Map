using System.Collections;
using System.Collections.Generic;
using UnityEngine;
# if UNITY_EDITOR
using UnityEditor;
# endif

public class CalibrationTargetDebugger : MonoBehaviour
{
    [Header("=== Refs ===")]
<<<<<<< HEAD:Unity/Assets/Scripts/CalibrationTargetDebugger.cs
    public Camera center_eye_ref;
    public Camera left_eye_ref;
    public Camera right_eye_ref;
    public Transform gaze_target_prefab;

    [Header("=== Results Writing ===")]
    public CSVWriter target_writer;
    public CSVWriter event_writer;
    public float time_between_targets = 5f;
    private bool _is_active = false;

=======
    public Transform head_ref;
    public Transform gaze_target_prefab;

>>>>>>> b942bf51a8469f25f79c2b903261e4c140ebf7a5:Assets/Scripts/CalibrationTargetDebugger.cs
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
<<<<<<< HEAD:Unity/Assets/Scripts/CalibrationTargetDebugger.cs
        if (center_eye_ref == null) return;
        Vector3 v = center_eye_ref.transform.rotation * CalculateLocalVector(theta_degrees, phi_degrees, radius);
        Gizmos.color = Color.yellow;
        Gizmos.DrawLine(center_eye_ref.transform.position, center_eye_ref.transform.position + v);
        Gizmos.color = Color.grey;
        Gizmos.DrawSphere(center_eye_ref.transform.position + v, 0.15f);
=======
        if (head_ref == null) return;
        Vector3 v = head_ref.rotation * CalculateLocalVector(theta_degrees, phi_degrees, radius);
        Gizmos.color = Color.yellow;
        Gizmos.DrawLine(head_ref.position, head_ref.position + v);
        Gizmos.color = Color.grey;
        Gizmos.DrawSphere(head_ref.position + v, 0.15f);
        //gaze_position_ref.position = head_ref.position + v;
        //gaze_position_ref.rotation = Quaternion.LookRotation(-v);
>>>>>>> b942bf51a8469f25f79c2b903261e4c140ebf7a5:Assets/Scripts/CalibrationTargetDebugger.cs
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
<<<<<<< HEAD:Unity/Assets/Scripts/CalibrationTargetDebugger.cs
        if (center_eye_ref == null) {
=======
        if (head_ref == null) {
>>>>>>> b942bf51a8469f25f79c2b903261e4c140ebf7a5:Assets/Scripts/CalibrationTargetDebugger.cs
            Debug.LogError("Cannot instantiate new target if reference to the user's head is missing.");
            return;
        }

        // Calculate relative position
<<<<<<< HEAD:Unity/Assets/Scripts/CalibrationTargetDebugger.cs
        Vector3 v = center_eye_ref.transform.rotation * CalculateLocalVector(theta_degrees, phi_degrees, radius);

        // Instantiate
        Transform t = Instantiate(gaze_target_prefab, center_eye_ref.transform.position + v, Quaternion.LookRotation(-v)) as Transform;
        t.SetParent(center_eye_ref.transform);
=======
        Vector3 v = head_ref.rotation * CalculateLocalVector(theta_degrees, phi_degrees, radius);

        // Instantiate
        Transform t = Instantiate(gaze_target_prefab, head_ref.position + v, Quaternion.LookRotation(-v)) as Transform;
        t.SetParent(head_ref);
>>>>>>> b942bf51a8469f25f79c2b903261e4c140ebf7a5:Assets/Scripts/CalibrationTargetDebugger.cs

        // Add to list of instantiated targets
        targets.Add(t);
    }

    public void RemoveTarget(Transform t) {
        targets.Remove(t);
        DestroyImmediate(t.gameObject);
    }

    void Start() {
        for(int i = 0; i < targets.Count; i++) {
<<<<<<< HEAD:Unity/Assets/Scripts/CalibrationTargetDebugger.cs
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

        // Step 0: Disable the ability to run another calibration
        _is_active = true;

        // Step 1: Activate writer
        target_writer.Initialize();

        // Write a line for each calibration target
        for(int i = 0; i < targets.Count; i++) {
            int target_number = i;
            Transform t = targets[i];

            // Get screen positions
            Vector3 left_screen_pos = left_eye_ref.WorldToScreenPoint(t.position);
            Vector3 center_screen_pos = center_eye_ref.WorldToScreenPoint(t.position);
            Vector3 right_screen_pos = right_eye_ref.WorldToScreenPoint(t.position);

            // Add Payloads
            target_writer.AddPayload(target_number);
            target_writer.AddPayload(t.position);          // world_pos
            target_writer.AddPayload(left_screen_pos);     // screen_left_pos
            target_writer.AddPayload(center_screen_pos);   // screen_center_pos
            target_writer.AddPayload(right_screen_pos);    // screen_right_pos

            // Writel ine
            target_writer.WriteLine();
        }

        // Final step: Deactivate writer
        target_writer.Disable();

        // Initialize calibration run
        StartCoroutine(CalibrationRun());
    }

    public IEnumerator CalibrationRun() {
        // Initialize event writer
        event_writer.Initialize();

        // Hide all calibration targets
        foreach(Transform t in targets) {
            t.gameObject.SetActive(false);
        }

        // Writer first line
        float start_time = Time.time;
        float start_frame = Time.frameCount;
        event_writer.AddPayload(0f);
        event_writer.AddPayload(0);
        event_writer.AddPayload("Start");
        event_writer.AddPayload("");
        event_writer.WriteLine();

        // Run Through Loop
        WaitForSeconds wait_event = new WaitForSeconds(time_between_targets);
        for(int i = 0; i < targets.Count; i++) {
            // Make this transform visible
            Transform t = targets[i];
            t.gameObject.SetActive(true);

            // Write to event
            event_writer.AddPayload(Time.time - start_time);
            event_writer.AddPayload(Time.frameCount - start_frame);
            event_writer.AddPayload("Target");
            event_writer.AddPayload(i);
            event_writer.WriteLine();

            // Wait 
            yield return wait_event;

            // Make invisible
            t.gameObject.SetActive(false);
        }

        // Write final line
        event_writer.AddPayload(Time.time - start_time);
        event_writer.AddPayload(Time.frameCount - start_frame);
        event_writer.AddPayload("End");
        event_writer.AddPayload("");
        event_writer.WriteLine();

        // Terminate event writer
        event_writer.Disable();

        // Re-enable all calibration targets
        foreach(Transform t in targets) {
            t.gameObject.SetActive(true);
        }

        // Re-enable ability to run through coroutine
        _is_active = false;
    }
=======
            CalibrationTarget t = targets[i].GetComponent<CalibrationTarget>();
            if (t != null) t.SetNumber(i);
        }
    }
>>>>>>> b942bf51a8469f25f79c2b903261e4c140ebf7a5:Assets/Scripts/CalibrationTargetDebugger.cs
}
