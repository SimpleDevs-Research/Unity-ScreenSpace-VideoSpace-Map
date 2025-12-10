import os
import shutil
import numpy as np
import cv2

# ------------------------------------------------------------
# HELPER FUNCTIONS : Not core functions, can be used anywhere
# ------------------------------------------------------------

# === Create directories indiscriminantly while deleting the older folder if it exists ===
#   Example:
#   outdir = mkdirs(os.path.join(trial['root_dir'], 'anchor_frames'))
def mkdirs(_DIR:str, delete_existing:bool=True):
    # If the folder already exists, delete it
    if delete_existing and os.path.exists(_DIR): shutil.rmtree(_DIR)
    # Create a new empty directory
    os.makedirs(_DIR, exist_ok=True)
    # Return the directory to indicate completion
    return _DIR

# === Given a root directory, find files with specific extensions ===
#   Example: 
#   videos = find_files_with_extensions(root_dir, ['.mov','.mp4'])
def find_files_with_extensions(dir:str, extensions):
    found_files = []
    for root, _, files in os.walk(dir):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() in [e.lower() for e in extensions]:  # Case-insensitive comparison
                found_files.append(os.path.join(root, file))
    return found_files

# === Convert lists or arrays into a serializable form for JSON conversion
#   Example:
#   positions = to_serializable(coords)
def to_serializable(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_serializable(i) for i in obj]
    else:
        return obj
    
# === Given a template image, find it in a source image ===
def estimate_template_from_image(src_img, 
                                 template_img, 
                                 min_size=10, 
                                 max_size=50, 
                                 delta_size=5, 
                                 thresh=0.9, 
                                 verbose=True):
    # Initialize bounding boxes
    bboxes = []
    # Iterate through possible sizes of the template, upwards to half of the size
    for p in np.arange(min_size, max_size, delta_size):
        # Resize the frame
        template_resize = cv2.resize(template_img, (p,p))
        # Get particular attributes of the image itself. 
        # We assume transparency, so we have to separate alpha from bgr
        template = template_resize[:,:,0:3]
        alpha = template_resize[:,:,3]
        alpha = cv2.merge([alpha,alpha,alpha])
        # get the width and height of the template
        h,w = template.shape[:2]
        # Prepare possible locations where the template matches
        loc = []
        # Find those matches.
        res = cv2.matchTemplate(src_img, template, cv2.TM_CCORR_NORMED, mask=alpha)
        # threshold
        loc = np.where(res >= thresh)
        if len(loc) > 0:
            for pt in zip(*loc[::-1]):
                bboxes.append((pt[0],pt[1],pt[0]+w,pt[1]+h, pt[0]+(w/2), pt[1]+(h/2)))
    # Print and return
    if verbose: print(f"# Detected Bounding Boxes: {len(bboxes)}")
    return bboxes
