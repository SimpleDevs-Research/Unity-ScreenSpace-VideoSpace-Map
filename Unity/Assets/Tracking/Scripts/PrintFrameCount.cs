using UnityEngine;
using TMPro;

public class PrintFrameCount : MonoBehaviour
{
    public TextMeshProUGUI textbox;

    // Update is called once per frame
    void Update() {
        if (textbox != null) textbox.text = Time.frameCount.ToString();
    }
}
