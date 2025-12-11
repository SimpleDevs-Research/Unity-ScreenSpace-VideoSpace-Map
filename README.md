# Eye-To-Screen Map

## Quick Facts

### Goals:

- To better understand how screen recordings differ between recording conditions (e.g. recording device, the IPD of the headset, and the presence of dynamic resolution.)
- To identify the optimal way to transform Unity-based positional data to video screen space coordinates.

</details>

### Findings:

- Meta devices cannot simultaneously **screencast** and **record video**. 
    - To initialize recording, you must record from the device viewing the screencast.
    - Mobile devices (iPhones, Androids) are optimal for recording, as the _Meta Horizon App_ ([iOS](https://apps.apple.com/us/app/meta-horizon/id1366478176), [Android](https://play.google.com/store/apps/details?id=com.oculus.twilight&hl=en_US)) comes with in-house recording functions in the app itself.
    - Meta's screen-casting function casts the screen from the **left eye**.
- A mapping operation from VR screen space to video space is possible, but has caveats.
    - Recordings do not differ based on the **dynamic resolution** setting in Unity. 
    - Adjusting the **IPD** produces slightly different recorddings, but the same mapping function is technically interchangeable if in a pinch.
    - **Device type** (e.g. Mac, Windows, iPhone, Android) are the most distinct causes of differences between recordings. Mapping operations MUST be re-calculated depending on recording device type.
    - Video recordings **do not necessarily align with frames from VR**. A different methodology is needed to connect video frames with Unity frames.


</details>

## Data Collection Pipeline

This is the suggested data collection pipeline, in summary form. For further details, please read [our Data Collection documentation (`doc` / `data_collection.md`)](./docs/data_collection.md) for further details.

### Part 1: Calibrating your recording

You need to find an optimal mapping between known points in the VR screen space and the video space. To do this, we suggest a **calibration** session where you render a known visual anchor onto the screen at distinct points. 

1. With a known anchor image, you render multiple versions of it in a blatantly obvious way to the camera in VR. We typically do this by rendering the image as a child of the VR camera, allowing the anchors to move relative to the camera.
2. You record those anchors' screen positions by using `Camera.WorldToScreenPoint()` and saving those transformed positions. Simultaneously, you record a video of that operation via screen casting.
3. In post, you extract the template positions relative to the video using computer vision.
4. With the multiple positions of your template in both VR screen space (`Camera.WorldToScreenpoint()`) and in video space (template maching via computer vision), you can find an optimal mapping programmatically.
5. Save the resulting transformation matrix for later use.

### Part 2: Recording from your VR app

With your transformation matrix enabling you to map screen space coordinates to video space coordinates, you can now expand your operation.

1. In your Unity scene, at every frame (or at whichever frequency you wish), record the positions of all desired GameObjects relative to the VR screen (`Camera.WorldToScreenPoint()`). Simultaneously, record your video via screen cast.
2. In post, you apply your transformation matrix operation to transform each screen space coordinate to video space coordinates.

This step is a bit more difficult due to the inherent problem of mapping video frames to Unity frames. To do this, we recommend rendering the current Unity frame in the video as a UI element and then using **OCR** to read the Unity frame number per video frame. This allows you to map the _detected_ Unity frame from each video frame to each GameObject's position in that respective Unity frame.

## Further Documentation

### Unity Build:

Please read [our Unity documentation]() for further details on how to run this repository in Unity.

- **Directory**: `./Unity/`
- **Unity Version**: `2022.3.46f1`
- **Dependencies**:
    - [UnityUtils - V1.3](https://github.com/SimpleDevs-Tools/UnityUtils) - see the **Version 1.3 release**.
    - [Meta SKD](https://assetstore.unity.com/packages/tools/integration/meta-xr-all-in-one-sdk-269657) - Optimal way to run Unity builds on Meta Quest devices.

</details>

### Post-Processing & Analysis:

Please read [our Analysis documentation]() for further details on how to run the necessary python scripts.