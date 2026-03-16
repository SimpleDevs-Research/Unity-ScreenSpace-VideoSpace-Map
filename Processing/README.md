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