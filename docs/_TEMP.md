## Observations Regarding Meta OS' Render Pipelines for Recording and Casting

### Recording Resolutions and Device Compatibility

_All recordings are conducted in Landscape mode (16:9)._

|Casting Device|OS|Display Resolution|Recording Resolution|
|:-|:-|:-:|:-:|
|Meta Quest Pro (v2.1.1033)|Android|`1800` x `1920` (per eye)|`1920` x `1080`|
|Motorola Razr+ 2024|Android|`2640` x `1080`|`2640` x `1472`|
|Moto G 64Gb - 2025|Android|`1604` x `720`|`1600` x `896`|
|iPhone Xr|iOS|`1792` x `828`|`1280` x `720`|
|iPad Pro 11in 2nd-Gen|iPad OS|`2388` x `1668`|`1280` x `720`|

When casting to multiple devices, output resolutions of recordings differ depending on casting device and OS type. Rules appear to apply differently between iOS/iPad OS and Android.

- Android appears to try its best to match the width, and then pad the height to match the 16:9 aspect ratio. It is likely that the output width is rounded to match multiples of 16, though this specificity has yet to be tested.
- The Apple ecosystem (iOS, iPadOS) appears to force a standardized video resolution - both recordings output to `1280` x `720` regardless of display resolution. In other words, the Apple ecosystem might enforce standard encoding presets.

### Rationale Behind OS-Based Differences #1: Platform-driven enforcement
A potential reason for these differences across OS types may be **platform-driven enforcement**.

- Android might be more flexible in general (more encoders, flexible permissions).
- The Apple ecosystem may enforce stricter encoding pipelines ([ReplayKit](https://developer.apple.com/documentation/ReplayKit), [AVFoundation](https://developer.apple.com/documentation/avfoundation/)).

---

### Rationale #2: Downsampling From a "Master" Signal

The Meta Quest Pro has a per-eye resolution of `1800` x `1920`. In fact, if you use an application like [scrcpy](https://github.com/genymobile/scrcpy) to capture the raw footage from the Android foundation that the Meta Quest systems are built on top of, you'll notice that the raw footage is actually projected and distorted to conform better to lens ergonomics. What the user sees in the display is the result of a projected display, in other words; there's a lot going on under the hood.

Nonetheless, the recorded footage captured directly from the in-built recording suite on the Meta Quest devices outputs at `1920` x `1080`. It is unknown if this is the raw footage before it gets projected for the user's display, or if this is re-corrected AFTER the projection. Nonetheless, it may be safe to assume that this `1920` x `1080` footage is the "master" reference for all footage that is recorded, regardless if it is done via the in-built recording suite or via a casting recording.

It may be that the order of operations is thus:

```
[Per-eye render buffers]
        ↓
[Eye selection + distortion correction]
        ↓
[Crop + normalize to 16:9]
        ↓
1920×1080 (canonical stream)
        ↓
┌───────────────┬───────────────┬───────────────┐
│ Quest record  │ Android cast  │ iOS cast      │
│ 1920×1080     │ up/downscale  │ 1280×720      │
└───────────────┴───────────────┴───────────────┘
```

Alternatively:

1. The Meta Quest system grabs the raw footage captured by the in-game virtual camera for both eyes.
2. The two "master signal" footages are projected and displayed to the user's eyes individually.
3. Depending on the recording setting (which eye are we recording from), the "master signal" footage is retrieved for the user's preferred eye and is recorded via the following methods:
    - **In-built Recording**: The raw "master signal" footage is saved. This will always by `1920` x `1080`.
    - **Android Casting**: The raw footage is re-scaled to match the dimensions of the device, while enforcing a 16:9 aspect ratio. The scaling is more flexible (flexible permissions, encoders) and is scaled on multiples of 16 (potentially - need to check).
    - **iOS/iPadOS Casting**: The raw footage is downscaled to a fix preset of `1280` x `720` (720p) potentially due to more rigid encoding enforcement ([ReplayKit](https://developer.apple.com/documentation/ReplayKit), [AVFoundation](https://developer.apple.com/documentation/avfoundation/)). This could also just be due to the closed-source nature of iOS/iPadOS preventing flexible encoding architecture.

### Android's Rendering Pipeline

Android-based systems (even the Meta Quest systems, which run on Android) might operate along the following pipeline:

```
App (Unity / Unreal / native VR)
        ↓
Per-eye render targets (distorted, wide FOV)
        ↓
VR compositor (timewarp, reprojection)
        ↓
System surface / display buffer  ← 📍 scrcpy taps here
        ↓
Lens distortion (hardware/display pipeline)
        ↓
Actual photons through lenses → your eyes
```

I add `scrcpy` here becuase I noticed that `scrcpy`'s footage contains heavy barrel distortion. If we assume this pipeline to be true and that `scrcpy` taps into the display buffer after the per-eye render targets and VR compositor step, then we can assume that `scrcpy` is capturing the footage right before the display passes (physically) through the pancake lenses of the Meta Quest devices; the pancake lenses un-distort the footage for our eyes to see, physically.

This opens the question: where is Meta Quest's in-built recording (or even just casting) stepping in on this process? There are two options:

- On an entirely separate rendering path than what `scrcpy` and the user sees.
- Somewhere before per-eye render targets and the app itself.

So in theory, there are two possible pipelines:

#### Possibility #1: a separate "spectator" camera

This implicates that any kind of recording is not conducted on the same buffer as the eyes.

```
App scene
   ↓
[Camera A] → VR eyes (distorted, wide FOV)
[Camera B] → Spectator view (rectilinear, 16:9)  ← 🎯 
```

#### Possibility #2: Tapping the eye buffer before distortion

```
Per-eye render (undistorted)
        ↓
[record here?]
        ↓
Apply distortion
```

However, this may be unlikely. This may be because per-eye buffers:

- Are not 16:9
- Have asymmetric FOVs
- Often include hidden/unused regions
- Don’t map cleanly to a flat video

In other words, we may still need some pre-processing to project the video stream into `1920` x `1080`, such as:

- Cropping
- Reprojection
- Possibly re-rendering

#### Final Opinion: The Final Render Pipeline

```
Scene
  ↓
VR rendering (per-eye, distorted)         ← for headset
  ↓
Compositor → display → scrcpy sees this

AND IN PARALLEL:

Scene
  ↓
Spectator/mirror camera (undistorted)
  ↓
1920×1080 output → recording / casting
```

> Question: This pipeline assumes that we're using a separate render pipeline purely for recording/casting. Have we abandoned the possibility of correcting an already-distorted footage?

We haven't exactly ruled out the possibility. In fact, we have two remaining hypotheses:

1. **Post-distortion capture**: We effectively are recording _after_ the distortion is applied (i.e. what is fed to the per-eye displays), which would require some "correction" back to a normal 16:9 video.
2. **Pre-distortion spectator view**: We use a separate render buffer and pipeline for recording/casting and never touch the distortion layers of the display pipeline.

It is _unlikely_ that H1 is the case. It'll effectively be VERYy computationally expensive to reverse all the distortion conducted on it while also potentially relying on reconstruction geometry and cropping/reframing. This process will inevitably:

- Lose information at the edges of the video.
- introduce visual artifacts
- be hard to enforce a 16:9 frame

This leaves H2 to be the likely process: that upon invoking a request to record or cast the user's display, a separate render buffer pipeline is invoked and all footage is simultaneously piped to this pipleline.

> Question: What assurances do we have that the per-eye renders for the display pipeline are not 16:9 by default?

To further elaborate on this concern, one big assumption we are making with both H1 and H2 is that the per-eye render buffers (the step after the direct feed from the game) are not in 16:9. However, if that assumptio was broken (i.e. they actually are enforcing a 16:9 render target), then it may be possible that the recording/casting pipelines are simply picking up the raw footage from there.

However, consider the following:

1. The Meta Quest systems have a unique requirement regarding display output. They must match a `1800` x `1920` per-eye resolution. This means that if the render buffers were actually 16:9, then the footage has to be re-projected from 16:9 to 9:16.
2. Distortion inherently loses information in the peripherals. This means that to prevent information loss, the render buffers must actually contain _extra_ pixels at the edges. This practice implies that the render buffers must go beyond pre-established aspect ratios.

So while it's no absolute guarantee that the recording/casting pipeline is simply grabbing pixels from prior to any kind of distortion in the eye buffers, _it's very unlikely_. It may be more computationally efficient (though not space efficient) to invoke two separate render pipelines - one for the display, and the other for the recording and casting.

### In totality..

Given what we've covered so far, the architecture may appear to be something similar to:

```
[Game / XR App]
        ↓
   Scene graph
        ↓
 ┌───────────────┬────────────────────┐
 ↓               ↓                    ↓
VR Eye Views   Capture View       (optional variants)
(distorted)    (rectilinear)      (1:1, 16:9, cinematic)

 ↓               ↓
Compositor      GPU buffer
 ↓               ↓
Display         Hardware encoder
(scrcpy sees)    ↓
                File (recording) / Network stream (casting)
```

The problem is that everything is _closed-source_... we do not have any guarantees that this is actually what goes on.




### Analysis Methodology

We derived that the simplest way to derive the differences across the various conditions is to measure the differences in the estimated transformation matrices in of themselves. In an ideal situation where two conditions are identical, their transformation matrices should be similar, if not identical. Thus, measuring differences in their transformation matrices is suitable. We quantify that difference through two methods: 1) pair-wise Frobenius Distance of transformation matrices between each possible pair of conditions, and 2) the Squared Frobenius Distance of transformation matrices across each possible pair of conditions.

Let $\{A_1, A_2, \ldots, A_n\}$ be the set of transformation matrices, where each $A_i \in \mathbb{R}^{m \times k}.$  We define the Frobenius Distance matrix $D \in \mathbb{R}^{n \times n}$ as:

$$
D_{ij} = \| A_i - A_j \|_F = \sqrt{\sum_{p=1}^{m} \sum_{q=1}^{k} (A_{i,pq} - A_{j,pq})^2 }
$$

Alternatively, we define the Squared Frobenius Distance matrix as:

$$
D_{ij} = \| A_i - A_j \|_F^2 = \sum_{p=1}^{m} \sum_{q=1}^{k} (A_{i,pq} - A_{j,pq})^2
$$


There are, naturally, some issues with this approach. Firstly, we need to contend with the reality that any operations that involve float-point precision such as `numpy.linalg.lstsq` may suffer very miniscule imprecisions that coalesce over time. Furthermore, there may always be the potential of ill-ranked matrices, null values, etc. We are fortunate that we need a relatively simple solution given that we are only measuring 2D coordinates. Finally, we recognize that the Frobenius Distance operation simplifies the comparison down to 1D values as opposed to a fuller analysis with 2D semantic structures. Nonetheless, we still believe there is value in utilizing the Frobenius Distance and Squared Frobenius Distance as rough measurements of differences between transformation matrices.

### Distance Heatmaps (clustered across features)

To best represent the pair-wise analysis, we've generated three diferent heatmaps depicting the differences. Darker colors correlate to smaller differences, while lighter colors represent greater differences. The naming structure of each column and row defines `<IPD>-<DYN. RES>-<DEVICE>`.

<div style="display:grid;grid-template-columns:repeat(3,1fr);gap: 1rem;align-items: start;">
<div><img src="./docs/ipd.png" /></div>
<div><img src="./docs/resolution.png" /></div>
<div><img src="./docs/device.png" /></div>
</div>

In summary, we can argue the following:

- Changing between dynamic resolution does NOT affect recording, so no need for a new transformation matrix
- Changing the IPD produces a minor change in transformation matrix, so a re-calculation is needed. However, in a punch, it may be okay to use the same transforamtion matrix.
- Switching recording devices DOES require a different transformation matrix

## Conclusion

It is relatively safe to utilize Dynamic Resolution in Unity. However, changes in IPD and device recording methodology entail different calibrations. Due to the inherent variability in users' IPDs, it might be ideal to pre-compute the IPD of each possible IPD value across different headsets and utilize them when necessary. In a pinch one may be able to use a different calibration setting if the IDPs are relatively similar to one another, but it is not the ideal situation.

We generally recommend that you calibrate based on left screen positioning, for both the calibration and for estimation.