using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class CalibrationTarget : MonoBehaviour
{

    [Header("=== REFS ===")]
    public TextMeshProUGUI textbox;

    public void SetNumber(int n) {
        textbox.text = n.ToString();
    }
}
