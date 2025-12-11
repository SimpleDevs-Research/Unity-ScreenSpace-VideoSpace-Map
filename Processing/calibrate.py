import cv2
import os
import numpy as np 
import os
import pandas as pd
from tqdm import tqdm
import argparse
import helpers as h
import ocr
import warnings
from classes import Trial, CFrame, Transformer
pd.options.mode.chained_assignment = None  # default='warn'
warnings.filterwarnings(
    "ignore",
    message="'pin_memory' argument is set as true but not supported on MPS"
)

# ------------------------------------------------------------
# CALIBRATION: Given a trial, calibrate it! Outputs a trial with a Transformer;
# The transformer is cached and saved inside of the trial's directory.
# This can be referenced as an example of generating transformers for use elsewhere.
# ------------------------------------------------------------

# === Calibrate a Trial ===
# Ensures that a trial can be calibrated 
def calibrate_trial(trial:Trial, 
                    anchor_filepath:str,
                    video_filename:str, 
                    targets_filename:str,
                    vr_x_colname:str="left_screen_pos_x",
                    vr_y_colname:str="left_screen_pos_y",
                    validate:bool=True,
                    verbose:bool=True):
        
        # Assertions for necessary files
        video_filepath = os.path.join(trial.root_dir, video_filename)
        targets_filepath = os.path.join(trial.root_dir, targets_filename)
        assert os.path.exists(anchor_filepath), f"Anchor image '{anchor_filepath}' does not exist."
        assert os.path.exists(video_filepath), f"Requested video '{video_filename}' does not exist in the root directory"
        assert os.path.exists(targets_filepath), f"Gaze Targets CSV '{targets_filename}' does not exist in the root directory"

        # set up tqdm as a progress bar
        total_steps = 6 if validate else 5
        pbar = tqdm(total=total_steps)

        # Combining csv files
        pbar.set_description(f"Aggregating events and gaze targets...")
        targets_df = pd.read_csv(targets_filepath)
        tdf = targets_df[~targets_df['event'].isin(['Start','End'])]  # Remove start and end rows
        tdf["target_number"] = tdf["target_number"].astype(int)     # Typcast target number as int
        df = tdf.drop(columns=['unix_ms'])                  # Remove unix milliseconds from gaze targets
        target_frames = df.set_index('frame').to_dict(orient="index")
        print(target_frames.keys())
        pbar.update(1)

        # Extract frames from the calibration video
        pbar.set_description(f"Setting up video calibration frame extraction...")
        cap = cv2.VideoCapture(video_filepath)  # Get a cpature window
        assert cap.isOpened(), f"Could not open video '{video_filename}'"

        bbox_min, bbox_max = ocr.frame_count_bounding_box(video_filepath) # bounding box for ocr
        frames = []                             # Initialize collection of frames
        pbar.update(1)
        
        # Iterate through all frames
        pbar.set_description(f"Extracting frames...")
        fidx, success = 0, True
        target_number_index = 0
        target_frame_keys = list(target_frames.keys())
        while success:
            # Read frame from video, exit early if issue arises
            ok, _frame = cap.read() # Read frame
            if not ok: 
                print(f"\tWarning: Unable to read frame w/ idx {fidx}. Ending frame analysis")
                break
            # Extract frame number
            vr_frame_number, is_int = h.check_frame_number(_frame, bbox_min, bbox_max, return_frames=False)
            # Handle if it is one of our target frames
            if is_int and int(vr_frame_number) > target_frame_keys[target_number_index]:
                # Confirm which target frame is associated with 
                row = target_frames[target_frame_keys[target_number_index]]
                vr_coords = (row[vr_x_colname], row[vr_y_colname])  # Get screen position in VR
                frame = CFrame(row['target_number'], vr_coords=vr_coords)   # Create frame, cache it
                frame.set_frame(_frame)
                frames.append(frame)
                target_number_index += 1
            # Once we've confirmed we've hit all the targets, we bail
            if target_number_index == len(target_frame_keys):
                if verbose: print(f"\tAll target reference frames detected. Ending frame analysis.")
                break
        cap.release()   # Release capture
        assert len(frames) > 0, "No frames detected! Terminating early"
        pbar.update(1)

        # Template Search
        pbar.set_description(f"Template matching...")
        anchor_img = cv2.imread(anchor_filepath, cv2.IMREAD_UNCHANGED)
        trial.transformer = Transformer(name="transformer") # Init transformer class
        for frame in frames:
            # Calculate bounding boxes and their centroids
            frame.set_bboxes(h.estimate_template_from_image(frame.frame, anchor_img, verbose=verbose))
            _, median_center = frame.get_centroids()
            frame.img_coords = median_center
            # Append coords to transformer
            trial.transformer.add_vr_coords(frame.vr_coords)
            trial.transformer.add_img_coords(frame.img_coords)
        pbar.update(1)

        # Calculate transformation matrix
        pbar.set_description(f"Calculating the transformation matrix...")
        trial.transformer.calculate_transform()
        pbar.update(1)

        # Save Trial and transformer for later use
        trial.save_json(verbose=verbose)
        #trial.transformer.save_json(output_path=os.path.join(trial.root_dir, 'transformer.json'), verbose=verbose)

        # As validation, output frames with estimated coords, if prompted
        if validate:
            pbar.set_description(f"Validating the transformation matrix...")
            validation_outdir = h.mkdirs(os.path.join(trial.root_dir, 'calibrations'))
            validation_errors = []
            for frame in frames:
                vr_coords = frame.vr_coords
                img_coords = frame.img_coords
                estimation = trial.transformer.screen_to_frame(frame.vr_coords)
                outframe = frame.draw_marker(img_coords, color=[225,255,0], marker=cv2.MARKER_DIAMOND)
                outframe = frame.draw_marker(vr_coords, frame=outframe, color=[255,255,0], marker=cv2.MARKER_CROSS)
                outframe = frame.draw_marker(estimation, frame=outframe, color=[0,0,0], marker=cv2.MARKER_TILTED_CROSS)
                cv2.imwrite(os.path.join(validation_outdir, f"{frame.name}.jpg"), outframe)
                validation_errors.append({'frame':frame.name, 'error': np.sqrt((estimation[0] - img_coords[0])**2 + (estimation[1] - img_coords[1])**2)})
            validation_df = pd.DataFrame(validation_errors)
            validation_df.to_csv(os.path.join(validation_outdir, 'calibration_errors.csv'), index=False)
            pbar.update(1)

        # Terminate
        pbar.set_description("Operations complete!")
        return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root_dir', help="Relative directory to your trial", type=str)
    parser.add_argument('name', help="Trial name", type=str)
    parser.add_argument('-vf', '--video_filename', help="Fileame of the video file, including extension, relative to the trial dir", type=str, default="calibration.mp4")
    parser.add_argument('-tf', '--targets_filename', help="Filename of the targets csv file, including extension, relative to the trial dir", type=str, default="calibration.csv")
    args = parser.parse_args()

    trial = Trial(
        root_dir=args.root_dir,
        trial_name=args.name, 
    )
    calibrate_trial(trial,
                    './anchor.png',
                    args.video_filename,
                    args.targets_filename,
                    verbose=False )