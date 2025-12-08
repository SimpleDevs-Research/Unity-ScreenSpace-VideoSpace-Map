using UnityEngine;
using UnityEditor;

[CustomEditor(typeof(CalibrationTarget))]
public class CalibrationTargetEditor : Editor
{
    CalibrationTarget ct;

    public void OnEnable() {
        ct = (CalibrationTarget)target;
    }

    public override void OnInspectorGUI() {
        DrawDefaultInspector();

        // Don't do anything if not playing
        if (Application.isPlaying) return;

        // Render controls for each scene
        EditorGUILayout.LabelField("=== scene Controls ===", EditorStyles.boldLabel);
        SceneButtons();
    }  

    public void SceneButtons() {

        // Start a horizontal group for the buttons
        GUILayout.BeginHorizontal();

        if (GUILayout.Button("Straighten Rotation")) ct.Straighten();
        GUILayout.Space(5);
        if (GUILayout.Button("Rotate to Init")) ct.RotateToInit();

        // End the horizontal group
        GUILayout.EndHorizontal();
    }
}
