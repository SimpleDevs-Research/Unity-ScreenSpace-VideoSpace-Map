using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class CalibrationTarget : MonoBehaviour
{

    [Header("=== REFS ===")]
    public TextMeshProUGUI textbox;
    public Quaternion init_rotation;

    public void SetNumber(int n) {
        textbox.text = n.ToString();
    }

    public void Straighten() {
        transform.rotation = Quaternion.Euler(0f, 180f, 0f);
    }
    public void RotateToInit()
    {
        transform.rotation = init_rotation;
    }
}
