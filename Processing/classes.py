import os
import numpy as np
import json
import cv2
import helpers as h

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
    def save_json(self, output_dir:str, indent:int=2, verbose:bool=True):
        output = {
            'name': self.name,
            'vr_coords':h.to_serializable(self.vr_coords),
            'img_coords':h.to_serializable(self.img_coords),
            'transform':h.to_serializable(self.transform)
        }
        outpath = os.path.join(output_dir, self.name+".json")
        with open(outpath, "w") as outfile:
            json.dump(output, outfile, indent=indent)
        if verbose:
            print(f"\tTransformation Matrix calculated and saved in '{outpath}'")
        return outpath
    
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
    def draw_marker(self, coords, frame=None, color=[0,0,0], marker=cv2.MARKER_CROSS, inplace:bool=False):
        outframe = frame.copy() if frame is not None else self.frame.copy()
        outframe = cv2.drawMarker(outframe, (int(coords[0]), int(coords[1])), color, marker, 20, 2)
        if inplace: self.frame = outframe
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
    def __init__(
        self, 
        root_dir:str, 
        trial_name=None, 
        transformer:Transformer=None, 
        json_src:str=None,
        start_buffer_ms:int=0.0
    ):
        self.root_dir = root_dir
        if json_src is not None and os.path.exists(os.path.join(self.root_dir, json_src)):   
            self.load_json(os.path.join(self.root_dir, json_src))
        else:
            self.trial_name = trial_name if trial_name is not None else os.path.basename(os.path.normpath(root_dir))
            self.transformer = transformer
            self.start_buffer_ms = start_buffer_ms
    
    # Loaders
    # ------------------------------------------
    def load_json(self, json_src:str):
        try:
            with open(json_src, 'r') as file:
                data = json.load(file)
                print(data)
                self.trial_name = data['trial_name']
                self.transformer = Transformer(json_src=os.path.join(self.root_dir, data['transformer'])) if 'transformer' in data and os.path.exists(os.path.join(self.root_dir, data['transformer'])) else None
                self.start_buffer_ms = data['start_buffer_ms']
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
    def set_start_buffer(self, start_buffer_ms:int):
        self.start_buffer_ms = start_buffer_ms

    # Savers
    # ------------------------------------------
    def save_json(self, outname:str=None, indent:int=2, save_transformmer:bool=True, verbose:bool=True):
        output = {
            'trial_name': self.trial_name,
            'transformer': os.path.relpath(self.transformer.save_json(output_dir=self.root_dir, verbose=verbose), self.root_dir) if save_transformmer and self.transformer is not None else "",
            'start_buffer_ms': self.start_buffer_ms,
        }
        if outname is None: outname = self.trial_name
        outpath = os.path.join(self.root_dir, f'{outname}.json')
        with open(outpath, "w") as outfile: 
            json.dump(output, outfile, indent=indent)
        if verbose:
            print(f"\tTrial saved in '{outpath}'")
        return outpath