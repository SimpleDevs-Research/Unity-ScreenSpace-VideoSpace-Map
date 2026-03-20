import re
import base64
from pathlib import Path
import os
import shutil
import numpy as np
import cv2
import string
import easyocr
reader = easyocr.Reader(['en'])

fourcc_to_ext = {
    # --- MP4 container codecs ---
    "mp4v": ".mp4",    # MPEG-4 Part 2
    "avc1": ".mp4",    # H.264 baseline/main/high
    "H264": ".mp4",    # alt H.264 tag
    "h264": ".mp4",
    "X264": ".mp4",
    "x264": ".mp4",
    "H265": ".mp4",    # H.265/HEVC
    "h265": ".mp4",
    "HEVC": ".mp4",
    "hevc": ".mp4",
    
    # --- AVI container codecs ---
    "XVID": ".avi",
    "DIVX": ".avi",
    "DX50": ".avi",
    "MJPG": ".avi",    # Motion JPEG
    "HFYU": ".avi",    # HuffYUV
    "FFV1": ".avi",    # Lossless FFmpeg codec
    "I420": ".avi",
    "YV12": ".avi",
    
    # --- MOV container codecs (common QuickTime tags) ---
    "avc1": ".mov",    # H.264 inside MOV
    "mp4v": ".mov",    # sometimes used inside MOV
    "jpeg": ".mov",    # MJPEG inside MOV
    "prores": ".mov",
    "apcn": ".mov",    # ProRes 422
    "apch": ".mov",    # ProRes 422 HQ
    "apco": ".mov",    # ProRes 422 Proxy
    "apcs": ".mov",    # ProRes 422 LT
    "ap4h": ".mov",    # ProRes 4444
    
    # --- Matroska (MKV) container codecs ---
    "H265": ".mkv",
    "HEVC": ".mkv",
    "VP80": ".mkv",    # VP8
    "VP90": ".mkv",    # VP9
}

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

# === Checks whether a provided string value can be parsed as an integer
#   Example:
#   is_int = check_int("1123") <-- returns TRUE
def check_int(s:str):
    try: int(s)
    except ValueError: return False
    else: return True

# === Checks for a frame number in a provided image. Handles only raw video frames
# Returns the estimated frame number, if it's an int, and the outputted frames (if toggled) ===
#   Example:
# 
def check_frame_number(
        frame, crop_min, crop_max,
        threshold:int=125,
        return_frames:bool=True ):
    # Cropping (old formula: crop_h[0]:crop_h[1], crop_w[0]:crop_w[1])
    crop = frame[crop_min[1]:crop_max[1], crop_min[0]:crop_max[0]]
    # Grayscale & Binary Thresholding for easier processing
    grayscale = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    thr = cv2.threshold(grayscale, threshold, 255, cv2.THRESH_BINARY)[1]
    # OCR
    screen_text = reader.readtext(thr)
    conf_text = None
    is_int = False
    if len(screen_text) > 0:
        conf_text = screen_text[0][1]
        is_int = check_int(conf_text)
    if return_frames:
        return conf_text, is_int, crop, grayscale, thr
    return conf_text, is_int

# === Attempt to interpret the fourcc of an input video
def derive_fourcc_codec(cap, verbose:bool=True):
    fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
    f = [ chr((fourcc_int >> (8 * i)) & 0xFF) for i in range(4) ]
    codec = "".join(f)
    
    # Validate: must be printable ASCII
    if all(c in string.printable for c in codec):   
        if verbose: print("Detected codec:", codec)
    else:
        if verbose: print("Invalid codec detected, using mp4v instead")
        codec = "mp4v"
    return codec, fourcc_to_ext[codec]




# === Given a markdown file, transcripe it into Streamlit-compatible text
_DOC_TO_PAGE = {
    "docs/analysis.md": "Analysis_And_Results",
    "docs/methodology.md": "Methodology",
    "methodology.md": "Methodology",
    "docs/python.md": "Python",
    "python.md": "Python",
    "docs/templates_and_datasets.md": "About_Templates_And_Datasets",
    "templates_and_datasets.md": "About_Templates_And_Datasets",
}
def read_md_file(
        path:str, 
        separate_lines:bool=False,
        extract_header:bool=True
):
    # Pathlib version of the source path
    md_path = Path(path)
    # Read contents
    contents = open(path, 'r').read()

    """Helper function: Resolve pathing issues with urls"""
    def resolve_path(rel_path):
        # Skip external URLs
        if rel_path.startswith(("http://", "https://", "data:")):
            return rel_path
        # Resolve relative to markdown file
        abs_path = (md_path.parent / rel_path).resolve()
        if abs_path.exists():
            ext = abs_path.suffix.lower().replace(".", "")
            b64 = base64.b64encode(abs_path.read_bytes()).decode()
            return f"data:image/{ext};base64,{b64}"
        return rel_path

    # Fix HTML <img src="...">
    contents = re.sub( r'src=[\'"](.*?)[\'"]', lambda m: f'src="{resolve_path(m.group(1))}"', contents )
    # Fix Markdown images ![](…)
    contents = re.sub( r'!\[.*?\]\((.*?)\)', lambda m: m.group(0).replace(m.group(1), resolve_path(m.group(1))), contents )

    """Helper function: replace markdown urls to local pages with those from streamlit"""
    def replace_link(match):
        label, target = match.groups()
        target = target.lstrip("./")
        if target in _DOC_TO_PAGE:
            page = _DOC_TO_PAGE[target]
            return f"[{label}]({page})"
        return match.group(0)

    # Replace any markdown urls
    contents = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, contents)

    # Split the text based on newlines
    lines = contents.split("\n")

    # Return the appropriate version of the content
    if extract_header:
        header = lines[0].removeprefix("# ")
        return (header, "\n".join(lines[1:])) if not separate_lines else (header, lines[1:])
    return contents if not separate_lines else lines