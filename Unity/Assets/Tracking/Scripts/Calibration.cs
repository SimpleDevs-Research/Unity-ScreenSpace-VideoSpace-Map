using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Calibration : MonoBehaviour
{
    [Header("=== References ===")]
    [Tooltip("Anchors used for Calibration")]
    public Transform centerAnchor;
    public Transform topleftAnchor, toprightAnchor, bottomleftAnchor;
    [Space]
    [Tooltip("Scene Cameras")]
    public Camera leftCamera;
    public Camera rightCamera;
    public Camera centerCamera;
    [Tooltip("The writer from UnityUtils for record writing")]
    public CSVWriter writer;

    [Header("=== Settings ===")]
    [Tooltip("Should the calibrator begin from the start of the scene?")]
    public bool activateOnStart = true;
    [Tooltip("What background should we set for each eye upon start of the calibration?")]
    public Color backgroundColor = Color.white;
    [Tooltip("Should we even evoke a background color?")]
    public bool useBackground = true;
    [Tooltip("Should we deactivate the anchors upon finishing calibration?")]
    public bool deactivateAnchors = true;

    // =====================
    [Header("=== Outputs ===")]
    [SerializeField, Tooltip("Are we currently calibrating?")]
    private bool _calibrating = false;
    public bool calibrating => _calibrating;

    private IEnumerator calibrationCoroutine;
    

    void Start() {
        if (activateOnStart) Activate();
    }

    private IEnumerator CalibrationCoroutine() {
        // Let the system know that we're calibrating
        _calibrating = true;

        // If we want to use a background, make sure each eye has their backgrounds covered
        if (useBackground) {
            leftCamera.backgroundColor = backgroundColor;
            rightCamera.backgroundColor = backgroundColor;
            centerCamera.backgroundColor = backgroundColor;
        }

        // Add the center, topleft, topright, and bottomleft anchor positions relative to the screen
        Vector3 left_center = leftCamera.WorldToScreenPoint(centerAnchor.position);
        Vector3 left_topleft = leftCamera.WorldToScreenPoint(topleftAnchor.position);
        Vector3 left_topright = leftCamera.WorldToScreenPoint(toprightAnchor.position);
        Vector3 left_bottomleft = leftCamera.WorldToScreenPoint(bottomleftAnchor.position);
        Vector3 right_center = rightCamera.WorldToScreenPoint(centerAnchor.position);
        Vector3 right_topleft = rightCamera.WorldToScreenPoint(topleftAnchor.position);
        Vector3 right_topright = rightCamera.WorldToScreenPoint(toprightAnchor.position);
        Vector3 right_bottomleft = rightCamera.WorldToScreenPoint(bottomleftAnchor.position);
        Vector3 center_center = centerCamera.WorldToScreenPoint(centerAnchor.position);
        Vector3 center_topleft = centerCamera.WorldToScreenPoint(topleftAnchor.position);
        Vector3 center_topright = centerCamera.WorldToScreenPoint(toprightAnchor.position);
        Vector3 center_bottomleft = centerCamera.WorldToScreenPoint(bottomleftAnchor.position);

        // Initialize wait for seconds delay
        WaitForSeconds delay = new WaitForSeconds(3f);

        // Write Lines, then wait
        // Left Camera
        WriteRow("Left", "Center", left_center);
        WriteRow("Left", "Top Left", left_topleft);
        WriteRow("Left", "Top Right", left_topright);
        WriteRow("Left", "Bottom Left", left_bottomleft);
        // Right Camera
        WriteRow("Right", "Center", right_center);
        WriteRow("Right", "Top Left", right_topleft);
        WriteRow("Right", "Top Right", right_topright);
        WriteRow("Right", "Bottom Left", right_bottomleft);
        // Center Camera
        WriteRow("Center", "Center", center_center);
        WriteRow("Center", "Top Left", center_topleft);
        WriteRow("Center", "Top Right", center_topright);
        WriteRow("Center", "Bottom Left", center_bottomleft);
        // Wait for 3 seconds
        yield return delay;

        // Iterate through all anchors
        centerAnchor.gameObject.SetActive(true);
        topleftAnchor.gameObject.SetActive(false);
        toprightAnchor.gameObject.SetActive(false);
        bottomleftAnchor.gameObject.SetActive(false);
        yield return delay;

        centerAnchor.gameObject.SetActive(false);
        topleftAnchor.gameObject.SetActive(true);
        yield return delay;

        topleftAnchor.gameObject.SetActive(false);
        toprightAnchor.gameObject.SetActive(true);
        yield return delay;

        toprightAnchor.gameObject.SetActive(false);
        bottomleftAnchor.gameObject.SetActive(true);
        yield return delay;

        centerAnchor.gameObject.SetActive(true);
        topleftAnchor.gameObject.SetActive(true);
        toprightAnchor.gameObject.SetActive(true);
        bottomleftAnchor.gameObject.SetActive(true);
        yield return delay;

        // Set the trigger to let the system know that the coroutine has ended
        _calibrating = false;
        Deactivate();
    }

    public void Activate() {
        if (writer.is_active) {
            Debug.LogError("Cannot re-activate Calibration: writer is already active");
            return;
        }

        // Wait until writer is active
        if (writer.Initialize()) {
            // Add a single row to represent the start of the recording.
            writer.AddPayload("Activation");
            writer.AddPayload("");
            writer.AddPayload("");
            writer.AddPayload("");
            writer.AddPayload("");
            writer.AddPayload("");
            writer.WriteLine(true);
            
            // Initialize Coroutine
            calibrationCoroutine = CalibrationCoroutine();
            StartCoroutine(calibrationCoroutine);
        }
    }
    public void Deactivate() {
        // Stop the coroutine
        StopCoroutine(calibrationCoroutine);

        // Add final line
        writer.AddPayload("Deactivate");
        writer.AddPayload("");
        writer.AddPayload("");
        writer.AddPayload("");
        writer.AddPayload("");
        writer.AddPayload("");
        writer.WriteLine(true);

        // Disable writer
        writer.Disable();

        // Make sure all cameras have their colors reset.
        if (useBackground) {
            leftCamera.backgroundColor = new Color(0f,0f,0f,0f);
            rightCamera.backgroundColor = new Color(0f,0f,0f,0f);
            centerCamera.backgroundColor = new Color(0f,0f,0f,0f);
        }
        
        // Deactivate the anchors
        if (deactivateAnchors) {
            centerAnchor.gameObject.SetActive(false);
            topleftAnchor.gameObject.SetActive(false);
            toprightAnchor.gameObject.SetActive(false);
            bottomleftAnchor.gameObject.SetActive(false);
        }
    }

    private void WriteRow(string side, string anchorName, Vector3 pos) {
        string[] row = new string[] {
            "Anchor", 
            side,
            anchorName,
            pos.x.ToString(), 
            pos.y.ToString(), 
            pos.z.ToString() 
        };
        writer.AddPayload(row);
        writer.WriteLine(true);
    }

    void OnDestroy() {
        if (writer.is_active) Deactivate();
    }
}
