import json
import os
import numpy as np
import argparse
from classes import Calibration, Transformer

def rescale_transform(
    cal_filepath:str, 
    new_dims,
    new_filename:str,
    verbose:bool=True
):
    """
    Recompute an affine transform matrix for a resized video.
    """
    # open the original calibration file
    with open(cal_filepath) as f:
        data = json.load(f)

    # Extract the dimensions per-coordinate-wise
    orig_w, orig_h = data['transformer']['img_resolution']
    new_w, new_h = new_dims

    # Extract the img and vr coordinates from this data
    img_coords = np.array(data["transformer"]["img_coords"], dtype=float)
    vr_coords = np.array(data["transformer"]["vr_coords"], dtype=float)

    # Normalize coordinates to 0-1 space
    img_norm = img_coords.copy()
    img_norm[:, 0] /= orig_w
    img_norm[:, 1] /= orig_h

    # Scale into new video space
    img_scaled = img_norm.copy()
    img_scaled[:, 0] *= new_w
    img_scaled[:, 1] *= new_h

    # Recompute affine transform
    A = np.hstack([vr_coords, np.ones((vr_coords.shape[0], 1))])
    B = img_scaled

    # Create new Transformer
    transform, _, _, _ = np.linalg.lstsq(A, B, rcond=None)
    new_transform_obj = data['transformer'].copy()
    new_transform_obj['img_coords'] = img_scaled
    new_transform_obj['transform'] = transform
    transformer = Transformer(name='transformer', obj=new_transform_obj)

    # Create new Calibration
    cal_dir, cal_filename = os.path.split(cal_filepath)
    cal_name, cal_ext = os.path.splitext(cal_filename)
    new_calibration = Calibration(cal_dir, json_src=cal_filepath)
    new_calibration.set_transformer(transformer)

    # Save outputs
    new_cal_filepath = new_calibration.save_json(outname=new_filename, save_transformer=False, verbose=verbose)
    return new_cal_filepath

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Re-scale an existing calibration `.json` to match a different resolution.")
    parser.add_argument("calibration_filepath", help="Filepath to the calibration file to be re-scaled.", type=str)
    parser.add_argument('new_dims', help='The new dimensions (in pixels) to be scaled to. Requires two integer values', nargs=2, type=int)
    parser.add_argument('new_filename', help="The name of the new calibration session. The new calibration will be saved with this as its filename (excluding extension).", type=str)
    parser.add_argument('--verbose', help="Should we output print statements?", action="store_true")
    args = parser.parse_args()

    rescale_transform(
        args.calibration_filepath,
        args.new_dims,
        args.new_filename,
        verbose=args.verbose
    )

