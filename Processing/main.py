import cv2
import os
import numpy as np 
import os
import pandas as pd
import json
from tqdm import tqdm
import argparse
import helpers as h
pd.options.mode.chained_assignment = None  # default='warn'

# ------------------------------------------------------------
# CORE CLASSES: Classes specific to this repository
# ------------------------------------------------------------

# === Transformation Class ===
#   Defines the transformation matrix. Can be loaded from a json if needed.
#   The function `screen_to_frame()` is the transformation function from queried 
#       VR screen coordinates to frame coordinates.
class Transformer:
    def __init__(self, name:str=None, vr_coords=None, img_coords=None, transform=None, json_src:str=None, obj:object=None):
        if json_src is not None:    self.load_json(json_src)
        elif obj is not None:       self.load_obj(obj)
        else:
            self.name = name
            self.vr_coords = vr_coords
            self.img_coords = img_coords
            self.transform = transform
    
    # Loaders
    # ------------------------------------------
    def load_obj(self, obj:object):
        self.name = obj['name'] if 'name' in obj else None
        self.vr_coords = obj['vr_coords'] if 'vr_coords' in obj else None
        self.img_coords = obj['img_coords'] if 'img_coords' in obj else None
        self.transform = obj['transform'] if 'transform' in obj else None
    def load_json(self, json_src:str):
        try: 
            with open(json_src, 'r') as file:
                self.load_obj(json.load(file))
        except FileNotFoundError:
            print(f"Error: '{json_src}' not found.")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in '{json_src}'.")
        return self
    
    # Savers
    # ------------------------------------------
    def save_json(self, output_path:str, indent:int=2, verbose:bool=True):
        output = {
            'name': self.name,
            'vr_coords':h.to_serializable(self.vr_coords),
            'img_coords':h.to_serializable(self.img_coords),
            'transform':h.to_serializable(self.transform)
        }
        with open(output_path, "w") as outfile:
            json.dump(output, outfile, indent=indent)
        if verbose:
            print(f"\tTransformation Matrix calculated and saved in '{output_path}'")
    
    # Setters
    # ------------------------------------------
    def set_vr_coords(self, vr_coords):
        self.vr_coords = vr_coords
        return self
    def add_vr_coords(self, vr_coords):
        if self.vr_coords is None: self.vr_coords = []
        self.vr_coords.append(vr_coords)
    def set_img_coords(self, img_coords):
        self.img_coords = img_coords
        return self
    def add_img_coords(self, img_coords):
        if self.img_coords is None: self.img_coords = []
        self.img_coords.append(img_coords)
    
    # Calculators
    # ------------------------------------------
    def calculate_transform(self):
        assert self.vr_coords is not None, "VR Coordinates must be set first"
        assert self.img_coords is not None, "Img Coordinates must be set first"
        assert len(self.vr_coords) == len(self.img_coords), "Uneven number of coords between VR and Img coords"
        A = np.vstack([np.array(self.vr_coords).T, np.ones(len(self.vr_coords))]).T
        self.transform, res, rank, s = np.linalg.lstsq(A, self.img_coords, rcond=None)
        return self
    
    # Applications
    # ------------------------------------------
    def screen_to_frame(self, query_coords):
        assert self.transform is not None, "Your Transformer must have the transformation matrix set first"
        if len(query_coords) == 2:
            query_coords = [query_coords[0], query_coords[1], 1]
        return np.dot(query_coords, self.transform)


# === Frame Class ===
#   Generic class for frames. 
#   Allows for loading or saving of files
class Frame:
    def __init__(self, name):
        self.name = name

    # Loaders
    # ------------------------------------------
    def load_filepath(self, filepath:str, extract_name:bool=True):
        assert os.path.exists(filepath), f"Cannot load frame with an undefined filepath '{filepath}'"
        self.frame = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)
        if extract_name:
            base_name, _ = os.path.splitext(filepath)
            self.name = base_name
        return self
    
    # Setters
    # ------------------------------------------
    def set_frame(self, frame):
        self.frame = frame
        return self
    
    # Savers
    # ------------------------------------------
    def save_frame(self, filepath:str, use_name:bool=True):
        assert self.frame is not None, "Cannot save frame that is undefined"
        if use_name:
            dir = os.path.dirname(filepath)
            _, extension = os.path.splitext(filepath)
            filepath = os.path.join(dir, str(self.name)+extension)
        cv2.imwrite(filepath, self.frame)

    # Applications
    # ------------------------------------------
    def draw_marker(self, coords, frame=None, color=[0,0,0], marker=cv2.MARKER_CROSS):
        outframe = frame.copy() if frame is not None else self.frame.copy()
        outframe = cv2.drawMarker(outframe, (int(coords[0]), int(coords[1])), color, marker, 20, 2)
        return outframe

# === Calibration Frame Subclass ===
#   Inherited from parent `Frame` class. 
#   Specifically for calibration frames, which expect bounding boxes.
class CFrame(Frame):
    def __init__(self, name, vr_coords=None, img_coords=None, bboxes=None):
        Frame.__init__(self, name)
        self.vr_coords = vr_coords
        self.img_coords = img_coords
        self.bboxes = bboxes

    # Setters
    # ------------------------------------------
    def set_bboxes(self, bboxes):
        self.bboxes = bboxes
        return self
    
    # Getters
    # ------------------------------------------
    def get_centroids(self):
        assert self.bboxes is not None, "Cannot calculate centroids from bboxes that don't exist"
        mean_center = np.mean([[cx,cy] for (x1, y1, x2, y2, cx, cy) in self.bboxes], axis=0)
        median_center = np.median([[cx,cy] for (x1, y1, x2, y2, cx, cy) in self.bboxes], axis=0)
        return mean_center, median_center
    
    # Applications
    # ------------------------------------------
    def draw_bboxes(self, frame=None, bbox_color=[0,255,255], bbox_thickness=1, draw_centroids:bool=True, centroids_color=[0,255,255]):
        assert self.bboxes is not None, "Cannot draw bboxes that don't exist"
        outframe = frame.copy() if frame is not None else self.frame.copy()
        for (x1, y1, x2, y2, cx, cy) in self.bboxes:
            outframe = cv2.rectangle(outframe, (x1, y1), (x2, y2), bbox_color, bbox_thickness)
            if draw_centroids:
                outframe = cv2.drawMarker(outframe, (int(cx), int(cy)), centroids_color, cv2.MARKER_CROSS, 20, 2)
        return outframe
    def draw_mean_centroid(self, frame=None, color=[255,255,0], marker=cv2.MARKER_CROSS):
        assert self.bboxes is not None, "Cannot draw mean centroid from bboxes that don't exist"
        outframe = frame.copy() if frame is not None else self.frame.copy()
        center = np.mean([[cx,cy] for (x1, y1, x2, y2, cx, cy) in self.bboxes], axis=0)
        outframe = cv2.drawMarker(outframe, (int(center[0]), int(center[1])), color, marker, 20, 2)
        return outframe
    def draw_median_centroid(self, frame=None, color=[0,0,0], marker=cv2.MARKER_TILTED_CROSS):
        assert self.bboxes is not None, "Cannot draw mean centroid from bboxes that don't exist"
        outframe = self.frame.copy() if frame is None else frame.copy()
        center = np.median([[cx,cy] for (x1, y1, x2, y2, cx, cy) in self.template_bboxes], axis=0)
        outframe = cv2.drawMarker(outframe, (int(center[0]), int(center[1])), color, marker, 20, 2)
        return outframe
    

# === Trial Class ===
#   Technically a generic type, expects a root directory, a trial name, and a transformer. 
#   Can be loaded from a JSON file if needed. Can also save as a json.
class Trial:
    def __init__(self, root_dir:str, trial_name=None, transformer:Transformer=None, json_src:str=None):
        self.root_dir = root_dir
        if json_src is not None and os.path.exists(json_src):   
            self.load_json(json_src)
        else:
            self.trial_name = trial_name if trial_name is not None else os.path.basename(os.path.normpath(root_dir))
            self.transformer = transformer
    
    # Loaders
    # ------------------------------------------
    def load_json(self, json_src:str):
        try:
            with open(json_src, 'r') as file:
                data = json.load(file)
                self.trial_name = data['trial_name']
                self.video_filename = data['video_filename']
                self.transformer = Transformer(obj=data['transformer']) if 'transformer' in data else None
        except FileNotFoundError:
            print(f"Error: '{json_src}' not found.")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in '{json_src}'.")

    # Setters
    # ------------------------------------------
    def set_trial_name(self, trial_name):
        self.trial_name = trial_name
        return self
    def set_video_filename(self, video_filename:str):
        self.video_filename = video_filename
        return self
    def set_transformer(self, transformer:Transformer):
        self.transformer = transformer
        return self

    # Savers
    # ------------------------------------------
    def save_json(self, outname:str=None, indent:int=2):
        output = {
            'trial_name': self.trial_name,
            'video_filename':self.video_filename
        }
        if outname is None: outname = self.trial_name
        outpath = os.path.join(self.root_dir, f'{outname}.json')
        with open(outpath, "w") as outfile: 
            json.dump(output, outfile, indent=indent)
    
    # Calculations
    # ------------------------------------------
    def calibrate(self, 
                  anchor_filepath:str,
                  calibration_video_filename:str, 
                  calibration_events_filename:str,
                  calibration_targets_filename:str,
                  timestamp_offset:float=2, 
                  vr_x_colname:str="screen_center_pos_x",
                  vr_y_colname:str="screen_center_pos_y",
                  validate:bool=True,
                  verbose:bool=True):
        
        # Assertions for necessary files
        video_filepath = os.path.join(self.root_dir, calibration_video_filename)
        events_filepath = os.path.join(self.root_dir, calibration_events_filename)
        targets_filepath = os.path.join(self.root_dir, calibration_targets_filename)
        assert os.path.exists(anchor_filepath), f"Anchor image '{anchor_filepath}' does not exist."
        assert os.path.exists(video_filepath), f"Requested video '{calibration_video_filename}' does not exist in the root directory"
        assert os.path.exists(events_filepath), f"Events CSV '{calibration_events_filename}' does not exist in the root directory"
        assert os.path.exists(targets_filepath), f"Gaze Targets CSV '{calibration_targets_filename}' does not exist in the root directory"

        # set up tqdm as a progress bar
        total_steps = 6 if validate else 5
        pbar = tqdm(total=total_steps)

        # Combining csv files
        pbar.set_description(f"Aggregating events and gaze targets...")
        events_df = pd.read_csv(events_filepath)
        targets_df = pd.read_csv(targets_filepath)
        edf = events_df[~events_df['event'].isin(['Start','End'])]  # Remove start and end rows
        edf["target_number"] = edf["target_number"].astype(int)     # Typcast target number as int
        tdf = targets_df.drop(columns=['unix_ms'])                  # Remove unix milliseconds from gaze targets
        tdf["target_number"] = tdf["target_number"].astype(int)     # Typecast target number as int
        df = pd.merge(left=edf, right=tdf, on='target_number')      # Inner join
        pbar.update(1)

        # Extract frames from the calibration video
        pbar.set_description(f"Setting up video calibration frame extraction...")
        cap = cv2.VideoCapture(video_filepath)  # Get a cpature window
        assert cap.isOpened(), f"Could not open video '{calibration_video_filename}'"
        fps = cap.get(cv2.CAP_PROP_FPS)         # Get FPS
        frames = []                             # Initialize collection of frames
        pbar.update(1)
        
        # Iterate through all frames
        pbar.set_description(f"Extracting frames...")
        for _, row in df.iterrows():
            vr_coords = (row[vr_x_colname], row[vr_y_colname])  # Get screen position in VR
            target_time = row['timestamp'] + timestamp_offset   # Calculate the time based on offset
            frame_idx = int(target_time * fps)                  # Get the desired frame index at the offset time
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)         # Set the capture to 
            ok, _frame = cap.read()                             # Move on if unable to read frame
            if not ok:  
                print(f"\tWarning: Unable to read frame @ {target_time} | (frame {frame_idx}).")
                continue
            frame = CFrame(row['target_number'], vr_coords=vr_coords)   # Create frame, cache it
            frame.set_frame(_frame)
            frames.append(frame)
        cap.release()   # Release capture
        assert len(frames) > 0, "No frames detected! Terminating early"
        pbar.update(1)

        # Template Search
        pbar.set_description(f"Template matching...")
        anchor_img = cv2.imread(anchor_filepath, cv2.IMREAD_UNCHANGED)
        self.transformer = Transformer() # Init transformer class
        for frame in frames:
            # Calculate bounding boxes and their centroids
            frame.set_bboxes(h.estimate_template_from_image(frame.frame, anchor_img, verbose=verbose))
            _, median_center = frame.get_centroids()
            frame.img_coords = median_center
            # Append coords to transformer
            self.transformer.add_vr_coords(frame.vr_coords)
            self.transformer.add_img_coords(frame.img_coords)
        pbar.update(1)

        # Calculate transformation matrix
        pbar.set_description(f"Calculating the transformation matrix...")
        self.transformer.calculate_transform()
        self.transformer.save_json(output_path=os.path.join(self.root_dir, 'transformer.json'), verbose=verbose)
        pbar.update(1)

        # As validation, output frames with estimated coords, if prompted
        if validate:
            pbar.set_description(f"Validating the transformation matrix...")
            validation_outdir = h.mkdirs(os.path.join(self.root_dir, 'validations'))
            validation_errors = []
            for frame in frames:
                vr_coords = frame.vr_coords
                img_coords = frame.img_coords
                estimation = self.transformer.screen_to_frame(frame.vr_coords)
                outframe = frame.draw_marker(img_coords, color=[225,255,0], marker=cv2.MARKER_DIAMOND)
                outframe = frame.draw_marker(vr_coords, frame=outframe, color=[255,255,0], marker=cv2.MARKER_CROSS)
                outframe = frame.draw_marker(estimation, frame=outframe, color=[0,0,0], marker=cv2.MARKER_TILTED_CROSS)
                cv2.imwrite(os.path.join(validation_outdir, f"{frame.name}.jpg"), outframe)
                validation_errors.append({'frame':frame.name, 'error': np.sqrt((estimation[0] - img_coords[0])**2 + (estimation[1] - img_coords[1])**2)})
            validation_df = pd.DataFrame(validation_errors)
            validation_df.to_csv(os.path.join(validation_outdir, 'estimation_errors.csv'), index=False)
            pbar.update(1)

        # Terminate with self-return
        pbar.set_description("Operations complete!")
        return self
    
    def estimate():

# ------------------------------------------------------------
# CORE FUNCTIONS: Functions specific to this repository
# ------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root_dir', help="Relative directory to your trial", type=str)
    parser.add_argument('name', help="Trial name", type=str)
    parser.add_argument('-vf', '--video_filename', help="Fileame of the video file, including extension, relative to the trial dir", type=str, default="video.mp4")
    parser.add_argument('-ef', '--events_filename', help="Filename of the events csv file, including extension, relative to the trial dir", type=str, default="events.csv")
    parser.add_argument('-tf', '--targets_filename', help="Filename of the targets csv file, including extension, relative to the trial dir", type=str, default="gaze_targets.csv")
    args = parser.parse_args()

    trial = Trial(
        root_dir=args.root_dir,
        trial_name=args.name, 
    )
    trial.calibrate(
        anchor_filepath = './anchor.png',
        calibration_video_filename = args.video_filename,
        calibration_events_filename = args.events_filename,
        calibration_targets_filename = args.targets_filename,
        verbose=False
    )
