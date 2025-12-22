using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Gyro_Accel : MonoBehaviour
{
    public enum UpdateType { FixedUpdate, Update }

    [Header("=== SETTINGS ===")]
    public UpdateType update_type = UpdateType.FixedUpdate;

    [Header("=== OUTCOMES ===")]
    [ReadOnlyInsp] public Vector3 gyroscope;
    [ReadOnlyInsp] public Vector3 local_gyroscope;
    [ReadOnlyInsp] public Vector3 acceleration;
    [ReadOnlyInsp] public Vector3 local_acceleration;

    private Quaternion prev_rotation;
    private Vector3 prev_position;
    private Vector3 prev_velocity;

    void Start() {
        prev_rotation = transform.rotation;
        prev_position = transform.position;
        prev_velocity = Vector3.zero;
    }

    void Update() {
        if (update_type == UpdateType.Update) Calculate(Time.deltaTime);
    }

    // Update is called once per frame
    void FixedUpdate() {
        if (update_type == UpdateType.FixedUpdate) Calculate(Time.fixedDeltaTime);
    }

    private void Calculate(float dt) {
        // Cache current stats
        Quaternion current_rotation = transform.rotation;
        Vector3 current_position = transform.position;

        // Calculate gyroscope and acceleration
        gyroscope = ComputeGyro(prev_rotation, current_rotation, dt);
        Vector3 vel = (current_position - prev_position) / dt;
        acceleration = ((vel - prev_velocity) / dt) - Physics.gravity;

        // Calculate local
        local_gyroscope = Quaternion.Inverse(current_rotation) * gyroscope;
        local_acceleration = Quaternion.Inverse(current_rotation) * acceleration;

        // Cache previous
        prev_rotation = current_rotation;
        prev_position = current_position;
        prev_velocity = vel;
    }

    public static Vector3 ComputeGyro(Quaternion prev, Quaternion current, float dt) {
        // Measure change in rotation from the previous rotation
        Quaternion dq = current * Quaternion.Inverse(prev);

        // Ensure shortest path
        if (dq.w < 0) {
            dq = new Quaternion(-dq.x, -dq.y, -dq.z, -dq.w);
        }

        // Get angle axis
        dq.ToAngleAxis(out float angleDeg, out Vector3 axis);

        // Consider when angle diff is greater than 180 degrees. We basically want to contain rotations between -180 and 180 degrees
        if (angleDeg > 180f) {
            angleDeg -= 360f;
        }

        // Calculate output gyroscope
        float angleRad = angleDeg * Mathf.Deg2Rad;
        return axis * (angleRad / dt);      // Radians per second
    }
}
