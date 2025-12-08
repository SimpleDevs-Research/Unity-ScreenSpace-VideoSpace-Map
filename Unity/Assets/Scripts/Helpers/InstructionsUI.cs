using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

[RequireComponent(typeof(CanvasGroup))]
public class InstructionsUI : MonoBehaviour
{

    public enum DisplayType { Off, Constant, Fade_In_Out, Fade_Out, Fade_In}

    [SerializeField]
    private Transform positionTarget = null;
    [SerializeField]
    private Transform lookAtTarget = null;
    private CanvasGroup canvasGroup;
    [SerializeField]
    private TextMeshProUGUI textbox = null;
    
    [SerializeField]
    private float movementSpeed = 1f;
    [SerializeField]
    private AnimationCurve movementMultiplier;
    [SerializeField]
    private DisplayType displayType = DisplayType.Fade_In_Out;
    private DisplayType _displayType;
    [SerializeField] private float distanceThreshold = 2f;
    [SerializeField] private float fadeTimeThreshold = 2f;
    [SerializeField] private float fadeTimeRate = 0.5f;

    private float startTime = 0f;
    private float distanceToTarget = 0f;
    private float gradientValue = 0f;
    private bool isClose = true;

    private void Awake() {
        startTime = Time.time;  // Time since the start of the application
        canvasGroup = GetComponent<CanvasGroup>();
        _displayType = displayType;
    }

    // Update is called once per frame
    void Update()
    {
        distanceToTarget = Vector3.Distance(positionTarget.position, transform.position);
        gradientValue = Mathf.Clamp(distanceToTarget/distanceThreshold, 0f, 1f);
        isClose = distanceToTarget <  0.05f;
        if (positionTarget != null) UpdatePosition();
        if (lookAtTarget != null) UpdateRotation();
        UpdateOpacity();
    }

    private void UpdatePosition() {
        if (isClose) {
            transform.position = positionTarget.position;
            return;
        }
        float step = movementSpeed * Time.deltaTime * movementMultiplier.Evaluate(gradientValue);
        transform.position = Vector3.MoveTowards(transform.position, positionTarget.position, step);
    }

    private void UpdateRotation() {
        transform.rotation = Quaternion.LookRotation(transform.position - lookAtTarget.position);
    }

    private void UpdateOpacity(float toSetAlpha=1f) {
        float newAlpha = toSetAlpha;
        switch(displayType) {
            case DisplayType.Fade_In_Out:
                newAlpha = (!isClose) ? 1f - gradientValue : 1f;
                break;
            case DisplayType.Constant:
                newAlpha = 1f;
                break;
            case DisplayType.Fade_Out:
                newAlpha = (Time.time - startTime < fadeTimeThreshold) 
                    ? 1f 
                    : 1f - Mathf.Clamp((Time.time - startTime+fadeTimeThreshold)/fadeTimeRate, 0f, 1f);
                break;
            case DisplayType.Fade_In:
                newAlpha = (Time.time - startTime < fadeTimeThreshold) 
                    ? 0f 
                    : Mathf.Clamp((Time.time - startTime+fadeTimeThreshold)/fadeTimeRate, 0f, 1f);
                break;
            default:
                // Off is the default
                newAlpha = 0f;
                break;
        }
        canvasGroup.alpha = newAlpha;
    }

    public void SetText(string newText) {
        if (textbox == null) {
            Debug.LogError("Cannot render text onto a nonexisting textbox");
            return;
        }
        if (newText == null || newText.Length == 0) {
            textbox.text = "";
            displayType = DisplayType.Off;
        } else {
            textbox.text = newText;
            displayType = _displayType;
        }
    }
}
