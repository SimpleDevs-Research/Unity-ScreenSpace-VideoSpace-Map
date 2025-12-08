using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;

[ExecuteInEditMode]
public class LineToChildren : MonoBehaviour
{
    public Color lineColor = Color.yellow;

    void OnDrawGizmos() {
        #if UNITY_EDITOR
        
        if(transform.childCount == 0) return;
        Gizmos.color = lineColor;
        foreach(Transform child in transform) {
            Gizmos.DrawLine(transform.position, child.position);
        }
        #endif
    }

    void Update() {
        //Debug.Log(transform.childCount);
    }
}