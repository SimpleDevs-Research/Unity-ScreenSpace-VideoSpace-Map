# Unity-Screen-Video-Map

## Motivations

We aim to better understand the operations of the Meta Quest's [casting](https://www.meta.com/help/quest/192719842695017/) and [recording](www.meta.com/help/quest/516228089650875/?srsltid=AfmBOorVsHW-ZEcP_t_wba_-YTMYAD8uUuCizR4yN9BC4NVCAMcX4h0u) functionality. These operations are crucial for VR-based human subject experimentation for a number of reasons - namely, ensuring that participants navigate virtual tasks correctly and recording virtual events for post-experiment analysis. One powerful affordance of this function is the possibility of computer vision-based analysis of VR events (e.g. object detection and tracking, eye tracking analysis).

However, due to Meta [restricting open access to their Meta Quest OS to third-party hardware developers](https://about.fb.com/news/2024/04/introducing-our-open-mixed-reality-ecosystem/), it is difficult to guarantee that any recording operations can be generalizable to different Meta HMDs, across different recording setups. This is potentially troublesome for reproducibility and ease-of-use for researchers who rely on vision-based analysis of VR events.

This project therefore aims to shed light on this obscure but crucial function provided by the Meta ecosystem. Though the results and insights gained from this analysis may be generalized to different HMD devices and ecosystems (e.g. the HTC Vive series), we emphasize that a significant part of this report is isolated to idiosyncracies pertaining to the Meta ecosystem.

#### Table of Contents

1. [Project Details](#1-project-details)
    1. [Definitions](#1a-definitions)
    2. [Major Goals](#1b-major-goals)
    3. [Minor Goals](#1c-minor-goals)
    4. [Factors Explored](#1d-factors-explored)
    5. [Deliverables](#1e-deliverables)
2. [How to Use This Package](#2-how-to-use-this-package)
    1. [Unity Build and Distribution](#2a-unity-build-and-distribution)
    2. [Core Operations](#2b-core-operations)

#### Additional Materials

We have additional documentation written down regarding this project:

- **[Methodology](docs/methodology.md)**: This page describes our methods to 1) record screen coordinates and video, with our Unity package as an example.
- **[Python Write-up](docs/python.md)**: Further detailed implementation details on the Python processing code provided in `src`.
- **[About Templates and Datasets](docs/templates_and_datasets.md)**: Additional notes about our pre-existing templates.
- **[Analysis and Results](docs/analysis.md)**: Our analysis and findings from this project, aggregated in a single document.

#### External References and Links

- [UnityUtils - V1.3.1](https://github.com/SimpleDevs-Tools/UnityUtils) - see the **Version 1.3.1 release**.
- [Meta SKD](https://assetstore.unity.com/packages/tools/integration/meta-xr-all-in-one-sdk-269657) - Optimal way to run Unity builds on Meta Quest devices.
- [Analysis Dataset & Pre-Calculated Templates](https://nyu.box.com/s/1gr9u1pw2twd3krbo60bin7m2yqat2pe)
    - Analysis datasets and figures are provided under `analysis/`
    - Templates are provided under 'templates/' and were recorded with as many devices as we could aggregate, under various settings. 
    - _Make sure to read [our notes on these templates and datasets](docs/templates_and_datasets.md) first though._

---

<h2 id="1-project-details">1. Project Details</h2>

<h4 id="1a-definitions">1a. Definitions</h4>

- **VR Screen Space**: Positions of objects within the 3D world space of a VR simulation, already ray-traced and mapped to the frame coordinates of virtual cameras meant to represent a VR user's eyes. In other words, we expect coordinates within this coordinate space to be 3-dimensional (x-axis pixel, y-axis pixel, distance-to-camera). 2-dimensional coordinates are also allowed.
- **Video Coordinate Space**: Video recordings of the VR space, whether they are recorded using an in-built recording suite (e.g. Meta's Camera/Casting system) or externally (e.g. OBS, Unity Screen Recording). Coordinates within this space are 2-dimensional (x-axis pixel, y-axis pixel).
- **Mapping**: Another way to describe the application of a transformation matrix to convert from screen to video coordinate space.

<h4 id="1b-major-goals">1b. Major Goals</h4>

1. Explore the _possibility_ to derive a transformation matrix to map screen coordinates to video coordinates.
2. Develop a _methodology_ to consistently reproduce transformation matrices across different recording setups.
3. Determine a transformation to _rescale_ between different recording setups.
4. Analyze the _effects_ of different recording hardware and settings on the "transferability" of calibrations.

<h4 id="1c-minor-goals">1c. Minor Goals</h4>

1. (_Within the Meta Horizons ecosystem_) Intuit the potential render pipelines used by the Meta Horizons and Meta Quest OS for display and recording rendering.
2. Create a web-based interface (e.g. Streamlit) for ease-of-use with core functions.
3. Release Unity packages for other users to calibrate their own setups.

<h4 id="1d-factors-explored">1d. Factors Explored</h4>

- **Interpupillary Distance (IPD)**: The distance between the centers of a user's pupils; the subsequent adjustment of hardware to accomodate for multiple IPDs (e.g. shifting the eye displays outward or inward to match the user's IPD) may lead to differences in screen space or video space coordinates.
- **Recording/Casting Device**: Does the device used to record footage from VR have an impact on the transformation matrix calculation?
- **HMD Device**: Do different HMDs have internal settings that produce different transformation matrices?

<h4 id="1e-deliverables">1e. Deliverables</h4>

- `Unity/` : The Unity Project used for development and testing.
- `SVM.apk` : A built version of the Unity project, which can be sideloaded into your Meta device (Meta Quest 2, Pro, and 3).
- `src/` : The Python scripts used for post-processing.
- `docs/`: Write-ups of our methodology, results, and python implementation.

---

<h2 id="2-how-to-use-this-package">2. How to Use This Package</h2>

<h4 id="2a-unity-build-and-distribution">2a. Unity Build and Distribution</h4>

The `Unity` directory is in of itself a Unity project. You can load this project directly into Unity and modify it for your personal needs.

- **Unity Version**: `2022.3.46f1`
- **Dependencies**:
    - [UnityUtils - V1.3.1](https://github.com/SimpleDevs-Tools/UnityUtils) - see the **Version 1.3.1 release**.
    - [Meta SKD](https://assetstore.unity.com/packages/tools/integration/meta-xr-all-in-one-sdk-269657) - Optimal way to run Unity builds on Meta Quest devices.

<h4 id="2b-core-operations">2b. Core Operations</h4>

This interface comes as a Streamlit application, which you can run with the following command (assuming you create a virtual environment and install all requirements provided in `requirements.txt`):

```bash
streamlit run app.py
```

Alternatively, all core functions are provided within the `src` folder. Please read our [python documentation](docs/python.md) for further notes on usage.
