using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using System.IO;
using System.Text;
using UnityEngine.XR;

public class GazeTrackRecorder : MonoBehaviour
{
    [Header("=== Writing Settings ===")]
    public bool activateOnStart = true;
    public CSVWriter writer;
    [Space]
    public float startTime = 0f;
    public float incrementTime = 1/60f;

    // =======================
    [Header("=== References ===")]
    public CombinedEyeTracker combinedEyeTracker;
    public Camera leftCamera, rightCamera, centerCamera;


    // =======================
    private IEnumerator updateCoroutine;
    

    private void Start() {
        if (activateOnStart) Activate();
    }

    public void Activate() {
        if (writer.is_active) {
            Debug.LogError("Cannot re-activate Gaze Track Recorder: writer is already active");
            return;
        }

        // Wait until writer is active
        if (writer.Initialize()) {
            updateCoroutine = RecordEyes();
            StartCoroutine(updateCoroutine);
        }
    }

    public void Deactivate() {
        StopCoroutine(updateCoroutine);
        // Add final line
        writer.AddPayload(GetCurrentTime());
        writer.AddPayload("");
        writer.AddPayload("Deactivate");
        writer.AddPayload("");
        writer.AddPayload("");
        writer.AddPayload("");
        writer.AddPayload("");
        writer.WriteLine(true);
        // Disable writer
        writer.Disable();
    }

    private IEnumerator RecordEyes() {
        // Initialize start time
        startTime = Time.time;

        // Add a single row to represent the start of the recording.
        writer.AddPayload(GetCurrentTime());
        writer.AddPayload("");
        writer.AddPayload("Activation");
        writer.AddPayload("");
        writer.AddPayload("");
        writer.AddPayload("");
        writer.AddPayload("");
        writer.AddPayload("");
        writer.WriteLine(true);

        // Initialize wait for seconds
        WaitForSeconds timeDelay = new WaitForSeconds(incrementTime);

        // Initialize loop
        while(true) {
            // Get world position of the eye, and convert to screen position
            Vector3 worldPos = combinedEyeTracker.rayTargetEndpoint;
            Vector3 leftScreenPos = leftCamera.WorldToScreenPoint(worldPos);
            Vector3 rightScreenPos = rightCamera.WorldToScreenPoint(worldPos);
            Vector3 centerScreenPos = centerCamera.WorldToScreenPoint(worldPos);
            
            // Get the target name
            string targetName = combinedEyeTracker.rayTargetName;

            // Get event
            string eventLabel = "";
            if (combinedEyeTracker.rayHit) eventLabel = "Eye Hit";
            
            // Left Eye Record
            writer.AddPayload(GetCurrentTime());
            writer.AddPayload(Time.frameCount);
            writer.AddPayload(eventLabel);
            writer.AddPayload("Left");
            writer.AddPayload(leftScreenPos);
            writer.AddPayload(targetName);
            writer.WriteLine(true);

            // Right Eye Record
            writer.AddPayload(GetCurrentTime());
            writer.AddPayload(Time.frameCount);
            writer.AddPayload(eventLabel);
            writer.AddPayload("Right");
            writer.AddPayload(rightScreenPos);
            writer.AddPayload(targetName);
            writer.WriteLine(true);

            // Center Eye Record
            // Left Eye Record
            writer.AddPayload(GetCurrentTime());
            writer.AddPayload(Time.frameCount);
            writer.AddPayload(eventLabel);
            writer.AddPayload("Center");
            writer.AddPayload(centerScreenPos);
            writer.AddPayload(targetName);
            writer.WriteLine(true);

            yield return timeDelay;
        }

        yield return null;
    }

    public float GetCurrentTime() {
        return Time.time - startTime;
    }

    void OnDestroy() {
        if (writer.is_active) Deactivate();
    }
}