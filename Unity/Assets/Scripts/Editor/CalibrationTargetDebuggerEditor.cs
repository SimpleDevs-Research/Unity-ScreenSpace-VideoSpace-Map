using UnityEngine;
using UnityEditor;

[CustomEditor(typeof(CalibrationTargetDebugger))]
public class CalibrationTargetDebuggerEditor : Editor
{
    CalibrationTargetDebugger debugger;

    public void OnEnable() {
        debugger = (CalibrationTargetDebugger)target;
    }

    public override void OnInspectorGUI() {
        DrawDefaultInspector();

        // Don't do anything if not playing
        if (Application.isPlaying) return;

        // Render controls for each scene
        EditorGUILayout.LabelField("=== scene Controls ===", EditorStyles.boldLabel);
        if (GUILayout.Button("Create New Target")) {
            debugger.CreateNewTarget();
        }
        foreach(Transform t in debugger.targets) {
            if (GUILayout.Button($"Unload \"{t.gameObject.name}\"")) {
                debugger.RemoveTarget(t);
            }
        }
    }  

    public void SceneButtons(Transform t) {

        // Start a horizontal group for the buttons
        GUILayout.BeginHorizontal();

        EditorGUILayout.LabelField(t.gameObject.name);
        GUILayout.Space(5);
        if (GUILayout.Button($"Unload \"{t.gameObject.name}\"")) {
            debugger.RemoveTarget(t);
        }

        // End the horizontal group
        GUILayout.EndHorizontal();
    }

}
