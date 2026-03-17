# Screen-Video-Map: Processing

## Installation

1. Create and run a new python environment
    ```bash
    python -m venv .venv

    source .venv/bin/activate
    .venv/Scripts/activate
    ```
2. Install all packages:
    ```bash
    pip install -r requirements.txt
    ```

## How to Run:

### Calibrating between Video and Calibration Targets:

```bash
python calibrate.py [-h] [-sb START_BUFFER] [-vf VIDEO_FILENAME] [-tf TARGETS_FILENAME] root_dir name
```

```
positional arguments:
  root_dir              Relative directory to your calibration trial
  name                  Calibration name

options:
  -h, --help            show this help message and exit
  -sb START_BUFFER, --start_buffer START_BUFFER
                        Buffer time (in seconds) from the video start where we should start processing the video
  -vf VIDEO_FILENAME, --video_filename VIDEO_FILENAME
                        Fileame of the video file, including extension, relative to the calibration trial dir
  -tf TARGETS_FILENAME, --targets_filename TARGETS_FILENAME
                        Filename of the targets csv file, including extension, relative to the calibration trial dir
```

### After Calibration, Estimate Given a Raw Set of Screen Positions

```bash
python estimate.py [-h] [-fc FRAME_COLNAME] [-xc X_COLNAME] [-yc Y_COLNAME] [-nxc NEW_X_COLNAME] [-nyc NEW_Y_COLNAME] [-od OUTPUT_DIRNAME] [-vp VIDEO_FILEPATH] [-sb START_BUFFER] [-p] [--verbose] calibration_filepath positions_filepath
```

```
positional arguments:
  calibration_filepath  Path to either the Transformer or Calibration `.json` file
  positions_filepath    Path to the the positions `.csv` file

options:
  -h, --help            show this help message and exit
  -fc FRAME_COLNAME, --frame_colname FRAME_COLNAME
                        The column name in your positions file corresponding to the frame number
  -xc X_COLNAME, --x_colname X_COLNAME
                        The column name in your positions file corresponding to the X coordinate in screen space
  -yc Y_COLNAME, --y_colname Y_COLNAME
                        The column name in your positions file corresponding to the Y coordinate in screen space
  -nxc NEW_X_COLNAME, --new_x_colname NEW_X_COLNAME
                        The NEW column name of the re-calibrated x-coord. If an empty string, it will default to `x_colname`
  -nyc NEW_Y_COLNAME, --new_y_colname NEW_Y_COLNAME
                        The NEW column name of the re-calibrated y-coord. If an empty string, it will default to `y_colname`
  -od OUTPUT_DIRNAME, --output_dirname OUTPUT_DIRNAME
                        Output directory relative to directory of either the positions filepath or video filepath; a new folder will be generated in the same location as your position/video file
  -vp VIDEO_FILEPATH, --video_filepath VIDEO_FILEPATH
                        Filepath to the video file you want to label. If left empty, then it will not produce a video.
  -sb START_BUFFER, --start_buffer START_BUFFER
                        Buffer time (in seconds) from the video start where we should start processing the video
  -p, --preview         If set, will preview transformations live
  --verbose             When generating videos, do we output messages to the log about progress?
```

## General Observations

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