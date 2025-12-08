using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CombinedEyeTracker : MonoBehaviour
{

    [Header("=== References ===")]
    public Transform headRef;
    public List<EyeTrackingRay> eyes = new List<EyeTrackingRay>();
    public Transform targetReticle = null;

    [Header("=== Settings ===")]
    public float rayDistance = 1f;
    public LayerMask layersToInclude;
    public float targetReticleSize = 1f;
    
    
    [Header("=== Outputs ===")]
    [SerializeField, Tooltip("Does either eye hit something?")] 
    private bool _rayHit = false;
    public bool rayHit => _rayHit;
    [SerializeField, Tooltip("Where is the theoretical eye endpoint, in world space?")] 
    private Vector3 _rayTargetEndpoint = Vector3.zero;
    public Vector3 rayTargetEndpoint => _rayTargetEndpoint;
    [SerializeField, Tooltip("What is the ray direction towards the ray target endpoint?")]
    private Vector3 _rayDir = Vector3.zero;
    public Vector3 rayDir => _rayDir;
    [SerializeField, Tooltip("The target hit position from the raycast")]
    private Vector3 _rayTargetPosition = Vector3.zero;
    public Vector3 rayTargetPosition => _rayTargetPosition;
    [SerializeField, Tooltip("The target hit name of the raycast")]
    private string _rayTargetName = "";
    public string rayTargetName => _rayTargetName;
    [SerializeField, Tooltip("Distance to the target hit")]
    private float _rayTargetDistance = 0f;
    public float rayTargetDistance => _rayTargetDistance;

    private void LateUpdate() {        
        // Use each eye to determine where the endpoint of the combined eye's ray should be, and figure out the ray from the head to that point
        _rayTargetEndpoint = Vector3.zero;
        foreach(EyeTrackingRay ray in eyes) {
            _rayTargetEndpoint += ray.rayTargetEndpoint;
        }
        _rayTargetEndpoint /= eyes.Count;
        _rayDir = (_rayTargetEndpoint - headRef.position).normalized;

        // Here we use raycast to determine target hit.
        // Initialize variables
        _rayHit = false;
        _rayTargetPosition = _rayTargetEndpoint;
        _rayTargetName = "";
        _rayTargetDistance = rayDistance;
        // Perform raycast
        RaycastHit hit;
        if (Physics.Raycast(headRef.position, _rayDir, out hit, rayDistance, layersToInclude)) {
            _rayHit = true;
            _rayTargetPosition = hit.point;
            _rayTargetName = hit.transform.gameObject.name;
            _rayTargetDistance = Vector3.Distance(hit.point, headRef.position);
        }

        /*
        // We want to 
        foreach(EyeTrackingRay ray in eyes) {
            _rayHit = _rayHit || ray.rayHit;
            rawRayDir = ray.rayTargetPosition - transform.position;
            _rayDir += rawRayDir.normalized;
            if (rayDistance == -1f || rawRayDir.magnitude < rayDistance) {
                rayDistance = rawRayDir.magnitude;
                _rayTargetName = ray.rayTargetName;
            }
        }
        _rayTargetPosition = transform.position + _rayDir.normalized*rayDistance;
        */
        
        // Set the target reticle
        if (targetReticle != null) {
            float targetScale = targetReticleSize * _rayTargetDistance;
            targetReticle.localScale = Vector3.one * targetScale;
            targetReticle.position = _rayTargetPosition;
        }
    }

    // This function will determine the combined eye tracker's eye target if all eyes agree on the target.
    private void FromBothEyes() {
        string tName = null;
        Vector3 avgPosition = Vector3.zero;
        for(int i = 0; i < eyes.Count; i++) {
            EyeTrackingRay ray = eyes[i];
            if (ray.rayHit) {
                
            }
        }
    }
}
