using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class IMU : MonoBehaviour
{
    public enum UpdateType { FixedUpdate, Update }

    [Header("=== SETTINGS ===")]
    public UpdateType update_type = UpdateType.FixedUpdate;
    [Help("If you record data, the program will auto-set all columns. All you need to modify is the filename and whether you want to write UNIX milliseconds")]
    public bool record = false;
    public CSVWriter writer;

    [Header("=== OUTCOMES ===")]
    [ReadOnlyInsp] public Vector3 gyroscope;
    [ReadOnlyInsp] public Vector3 acceleration;

    private int instance_id;
    private Quaternion prev_rotation;
    private Vector3 prev_position;
    private Vector3 prev_velocity;

    void Start() {
        // Cache data
        instance_id = gameObject.GetInstanceID();
        prev_rotation = transform.rotation;
        prev_position = transform.position;
        prev_velocity = Vector3.zero;

        // Initialize writer, if wanted
        writer.columns = new List<string>{
            "instance_id",
            "name",
            "timestamp",
            "frame",
            "gyro_x", "gyro_y", "gyro_z",
            "accel_x", "accel_y", "accel_z",
        };
        if (record) {
            // We'll actually set the column names ourselves
            writer.Initialize();
            Record();
        }
    }

    void Update() {
        if (update_type == UpdateType.Update) Calculate(Time.deltaTime);
        if (writer.is_active) Record();
    }

    // Update is called once per frame
    void FixedUpdate() {
        if (update_type == UpdateType.FixedUpdate) Calculate(Time.fixedDeltaTime);
        if (writer.is_active) Record();
    }

    private void Calculate(float dt) {
        // Cache current stats
        Quaternion current_rotation = transform.rotation;
        Vector3 current_position = transform.position;

        // Calculate gyroscope and acceleration
        Vector3 _gyroscope = ComputeGyro(prev_rotation, current_rotation, dt);
        Vector3 vel = (current_position - prev_position) / dt;
        Vector3 _acceleration = ((vel - prev_velocity) / dt) - Physics.gravity;

        // Calculate local
        gyroscope = Quaternion.Inverse(current_rotation) * _gyroscope;
        acceleration = Quaternion.Inverse(current_rotation) * _acceleration;

        // Cache previous
        prev_rotation = current_rotation;
        prev_position = current_position;
        prev_velocity = vel;
    }

    private void Record() {
        writer.AddPayload(instance_id);     // Instance ID
        writer.AddPayload(gameObject.name); // gameobject name
        writer.AddPayload(Time.time);       // Timestamp
        writer.AddPayload(Time.frameCount); // Frame Count
        writer.AddPayload(gyroscope);       // Gyroscope
        writer.AddPayload(acceleration);    // Acceleration
        writer.WriteLine();
    }

    void OnDestroy() {
        if (writer.is_active) writer.Disable();
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
