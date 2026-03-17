import cv2
import os
import numpy as np 
import os
import pandas as pd
import json
from tqdm import tqdm
import argparse
import warnings
import helpers as h
import ocr
from classes import Transformer, Frame

pd.options.mode.chained_assignment = None  # default='warn'
warnings.filterwarnings(
    "ignore",
    message="'pin_memory' argument is set as true but not supported on MPS"
)

def estimate(
    calibration_filepath:str,
    positions_filepath:str,
    frame_colname:str='frame',
    x_colname:str='left_screen_pos_x',
    y_colname:str='left_screen_pos_y',
    new_x_colname:str="video_x",
    new_y_colname:str="video_y",
    output_dirname:str='estimations',
):
    """
    Given a calibration setting and a dataset with positions that need to be calibrated, 
    Re-calibrate those positions. If a video is provided, create a new video with the 
    re-calculated positions embedded on top.
    """

    assert os.path.exists(calibration_filepath), "Calibration filepath (`.json`) not provided."
    assert os.path.exists(positions_filepath), "Positions filepath (`.csv`) not provided."

    # Attempt to load the calibration filepath as a json
    with open(calibration_filepath, 'r') as cfile:
        calibration_data = json.load(cfile)
    if 'transform' in calibration_data: 
        transformer = Transformer(obj=calibration_data)
    elif 'transformer' in calibration_data and 'transform' in calibration_data['transformer']:
        transformer = Transformer(obj=calibration_data['transformer'])
    else:
        raise ValueError("Provided calibration filepath does not lead to a `.json` file that is a proper transformer or calibration")

    # Attempt to read the positions filepath. Typecast the frame column as an integer type
    pdf = pd.read_csv(positions_filepath)
    pdf[frame_colname] = pdf[frame_colname].astype(int)

    # Re-calibrate by extracting the columns as a list of coords, then using Transformer to re-calibrate
    coords = list(zip(pdf[x_colname], pdf[y_colname]))
    cal_coords = transformer.screens_to_frames(coords)
    
    # Re-save the calibrated coordinates
    if new_x_colname is None: new_x_colname = x_colname
    if new_y_colname is None: new_y_colname = y_colname 
    pdf[[new_x_colname, new_y_colname]] = cal_coords

    # Output to a new directory to prevent mutation
    positions_dir, positions_filename = os.path.split(positions_filepath)
    output_dirpath = os.path.join(positions_dir, output_dirname)
    os.makedirs(output_dirpath, exist_ok=True)
    output_filepath = os.path.join(output_dirpath, positions_filename)
    pdf.to_csv(output_filepath, index=False)

    # Return the path to the outputted df
    return output_filepath

def label_video(
    video_filepath:str,
    positions_filepath:str,
    start_buffer_ms:int = 0,
    frame_colname:str = 'frame',
    x_colname:str = "video_x",
    y_colname:str = "video_y",
    preview:bool = False,
    output_dirname:str = 'estimations',
    verbose:bool = False

):
    assert os.path.exists(video_filepath), "Video filepath doesn't exist."
    assert os.path.exists(positions_filepath), "Positions filepath doesn't exist."

    # Get positions
    pdf = pd.read_csv(positions_filepath)
    assert set([x_colname, y_colname]).issubset(pdf.columns), f"Column names `{x_colname}` or `{y_colname}` don't exist in the provided positions dataframe (`.csv`)"

    # Prepare capture
    cap = cv2.VideoCapture(video_filepath)  # Get a cpature window
    assert cap.isOpened(), f"Could not open video '{video_filepath}'"
    cap.set(cv2.CAP_PROP_POS_MSEC, start_buffer_ms)
    fps    = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    #codec, output_ext = h.derive_fourcc_codec(cap, verbose=verbose)
    #fourcc = cv2.VideoWriter_fourcc(*codec)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_ext = '.mp4'

    # Prepare output video
    video_dir, video_filename = os.path.split(video_filepath)
    output_video_basename, output_video_extension = os.path.splitext(video_filename)
    output_dirpath = os.path.join(video_dir, output_dirname)
    os.makedirs(output_dirpath, exist_ok=True)
    output_filepath = os.path.join(output_dirpath, output_video_basename+output_ext)
    out = cv2.VideoWriter(output_filepath, fourcc, fps, (width, height))

    # Allow the user to select a bounding box for identifying frame counts in the video
    bbox_min, bbox_max = ocr.frame_count_bounding_box(video_filepath, start_buffer_ms=start_buffer_ms)
    print("ROI coordinates:", bbox_min, bbox_max)

    # Helper function: write the outframe.
    def write_frame(frame_number:int, outframe):
        # Find all rows where the frame number matches
        frame_positions = pdf[pdf[frame_colname]==frame_number]
        if len(frame_positions.index) > 0:
            # Extract the positions in vr screen space
            xs = frame_positions[x_colname].tolist()
            ys = frame_positions[y_colname].tolist()
            positions = list(zip(xs, ys))
            # we modify the outframe
            for coords in positions: 
                outframe.draw_marker(coords, color=[255,225,0], inplace=True)

    # Iterate through video frames. Open preview window if we are previewing
    fidx, success = 0, True
    if preview:     cv2.namedWindow("Position Labeling")
    while success:
        # Read frame from video, exit early if issue arises
        ok, frame = cap.read() # Read frame
        if not ok: 
            if verbose: print("\tEnding video labeling...")
            break
        # Copy the frame if outputting
        outframe = Frame(fidx)
        outframe.set_frame(frame.copy())
        # Use OCR to interpret VR frame index from video frame
        vr_frame_number, is_int = h.check_frame_number(frame, bbox_min, bbox_max, return_frames=False)
        # If we know it's an integer, strong likelihood that it's a frame.
        if is_int: write_frame(int(vr_frame_number), outframe)
        # Safety checks
        frame_to_write = outframe.frame
        frame_to_write = np.asarray(frame_to_write)
        if frame_to_write.dtype != np.uint8:
            frame_to_write = frame_to_write.astype(np.uint8)
        if frame_to_write.shape[:2] != (height, width):
            frame_to_write = cv2.resize(frame_to_write, (width, height))
        # Write to frame and preview
        out.write(frame_to_write)
        if preview: 
            cv2.imshow("Position Labeling", frame_to_write)
            cv2.waitKey(1)  # 1 ms delay
        # Update for the next frame
        fidx += 1
    # Reached the end, closing cap
    cap.release()
    if preview:     cv2.destroyWindow("Position Labeling")
    out.release()

    # Return the new video
    print(f"Labeling video {video_filepath}: Complete!")
    print(f"Newly labeled video saved in `{output_filepath}`")
    return output_filepath

"""
def estimate(
    trial:Trial, 
    positions_filename:str, 
    video_filename:str,
    frame_colname:str='frame',
    x_colname:str='left_screen_pos_x',
    y_colname:str='left_screen_pos_y',
    output_dirname:str='estimations',
    output_video:bool=False,
    preview:bool=False,
    verbose:bool=True
):
    
    # Assertions for necessary files and the Transformer
    positions_filepath = os.path.join(trial.root_dir, positions_filename)
    video_filepath = os.path.join(trial.root_dir, video_filename)
    assert os.path.exists(positions_filepath), f"Anchor image '{positions_filepath}' does not exist."
    assert os.path.exists(video_filepath), f"Requested video '{video_filepath}' does not exist in the root directory."
    assert trial.transformer is not None, "The trial does not have a Transformer set; make sure to assign a Transformer first."

    # Create output directory
    outdir = h.mkdirs(os.path.join(trial.root_dir, output_dirname))

    # Extract positions dataframe, for reference later
    pdf = pd.read_csv(positions_filepath)
    pdf[frame_colname] = pdf[frame_colname].astype(int)

    # Prepare video(s)
    cap = cv2.VideoCapture(video_filepath)  # Get a cpature window
    assert cap.isOpened(), f"Could not open video '{video_filename}'"
    cap.set(cv2.CAP_PROP_POS_MSEC, trial.start_buffer_ms)
    if output_video:
        output_video_basename, output_video_extension = os.path.splitext(video_filename)
        fps    = cap.get(cv2.CAP_PROP_FPS)
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        codec, output_ext = h.derive_fourcc_codec(cap, verbose=verbose)
        fourcc = cv2.VideoWriter_fourcc(*codec)
        output_video_filepath = os.path.join(outdir, output_video_basename+output_ext)
        out = cv2.VideoWriter(output_video_filepath, fourcc, fps, (width, height))

    # Allow the user to select a bounding box for identifying frame counts in the video
    bbox_min, bbox_max = ocr.frame_count_bounding_box(video_filepath, start_buffer_ms=trial.start_buffer_ms)
    print("ROI coordinates:", bbox_min, bbox_max)

    # Iterate through video frames. Open preview window if we are previewing
    fidx, success = 0, True
    reposition_dfs = []
    if preview:
        cv2.namedWindow("Position Estimation")
    while success:
        # Read frame from video, exit early if issue arises
        ok, frame = cap.read() # Read frame
        if not ok: 
            if verbose: print("\tEnding frame analysis")
            break
        # Copy the frame if outputting
        if output_video or preview:
            outframe = Frame(fidx)
            outframe.set_frame(frame.copy())
        # Use OCR to interpret VR frame index from video frame
        vr_frame_number, is_int = h.check_frame_number(frame, bbox_min, bbox_max, return_frames=False)
        # If we know it's an integer, strong likelihood that it's a frame. Let's process
        if is_int:
            # Find all rows where the frame number matches
            frame_positions = pdf[pdf[frame_colname]==int(vr_frame_number)]
            if len(frame_positions.index) > 0:
                # Extract the positions in vr screen space
                xs = frame_positions[x_colname].tolist()
                ys = frame_positions[y_colname].tolist()
                positions = list(zip(xs, ys))
                # Transform the vr screen space coords to video coords
                repositions = [trial.transformer.screen_to_frame(p) for p in positions]
                rx, ry = zip(*repositions)
                frame_positions['video_x'] = rx
                frame_positions['video_y'] = ry
                # Cache the results
                reposition_dfs.append(frame_positions)
                # If we are outputting, we modify the outframe
                if output_video or preview:
                    for rp in repositions: 
                        outframe.draw_marker(rp, color=[255,225,0], inplace=True)
        # if we are outputting, write the frame
        if output_video: out.write(outframe.frame)
        if preview: 
            cv2.imshow("Position Estimation", outframe.frame)
            cv2.waitKey(1)  # 1 ms delay
        fidx += 1
    # Reached the end, closing cap
    cap.release()
    if preview:
        cv2.destroyWindow("Position Estimation")

    # Outputting results
    rpdf = pd.concat(reposition_dfs, axis=0)
    rpdf.to_csv(os.path.join(outdir, 'repositions.csv'), index=0)
    if output_video: out.release()

    # Close and return
    return rpdf
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('calibration_filepath', help="Path to either the Transformer or Calibration `.json` file", type=str)
    parser.add_argument('positions_filepath', help="Path to the the positions `.csv` file", type=str)
    parser.add_argument('-fc', '--frame_colname', help="The column name in your positions file corresponding to the frame number", type=str, default='frame')
    parser.add_argument('-xc', '--x_colname', help="The column name in your positions file corresponding to the X coordinate in screen space", type=str, default='left_screen_pos_x')
    parser.add_argument('-yc', '--y_colname', help="The column name in your positions file corresponding to the Y coordinate in screen space", type=str, default='left_screen_pos_y')
    parser.add_argument('-nxc', '--new_x_colname', help="The NEW column name of the re-calibrated x-coord. If an empty string, it will default to `x_colname`", type=str, default='video_x')
    parser.add_argument('-nyc', '--new_y_colname', help="The NEW column name of the re-calibrated y-coord. If an empty string, it will default to `y_colname`", type=str, default='video_y')
    parser.add_argument('-od', '--output_dirname', help="Output directory relative to directory of either the positions filepath or video filepath; a new folder will be generated in the same location as your position/video file", type=str, default='estimations')
    # Video stuff - completely optional
    parser.add_argument('-vp', '--video_filepath', help="Filepath to the video file you want to label. If left empty, then it will not produce a video.", type=str, default="")
    parser.add_argument('-sb', '--start_buffer', help="Buffer time (in seconds) from the video start where we should start processing the video", type=float, default=0.0)
    parser.add_argument('-p', '--preview', help="If set, will preview transformations live", action="store_true")
    parser.add_argument('--verbose', help="When generating videos, do we output messages to the log about progress?", action="store_true")
    args = parser.parse_args()

    # Step 1: Estimate
    new_x_colname = args.new_x_colname if len(args.new_x_colname)>0 else args.x_colname
    new_y_colname = args.new_y_colname if len(args.new_y_colname)>0 else args.y_colname
    df_path = estimate(
        args.calibration_filepath,
        args.positions_filepath,
        frame_colname = args.frame_colname,
        x_colname = args.x_colname,
        y_colname = args.y_colname,
        new_x_colname = new_x_colname,
        new_y_colname = new_y_colname,
        output_dirname = args.output_dirname
    )

    # Step #2 (Optional): Apply to a video
    if args.video_filepath is not None and len(args.video_filepath)>0:
        label_video(
            args.video_filepath,
            df_path,
            start_buffer_ms=args.start_buffer * 1000,
            frame_colname = args.frame_colname,
            x_colname = new_x_colname,
            y_colname = new_y_colname,
            preview = args.preview,
            output_dirname= args.output_dirname,
            verbose = args.verbose
        )

    """
    estimate(
        trial, 
        args.positions_filename, 
        args.video_filename, 
        x_colname=args.x_colname,
        y_colname=args.y_colname,
        output_dirname=args.output_dirname, 
        output_video=args.output_video, 
        preview=args.preview, 
        verbose=True 
    )
    """
