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

def transform_screen_positions(
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

    # Correct the new colnames
    new_x_colname = new_x_colname if len(new_x_colname)>0 else x_colname
    new_y_colname = new_y_colname if len(new_y_colname)>0 else y_colname

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
    print(f"Transformed positions saved in `{output_filepath}`.")
    return output_filepath

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Given a transformation matrix calculated using `calibrate.py` (or by using one of our pre-calculated templates) and the screen space positions of one or more objects that need to be transformed, then this script effectively transforms those coordinates into video space.")
    parser.add_argument('calibration_filepath', help="Path to either the Transformer or Calibration `.json` file", type=str)
    parser.add_argument('positions_filepath', help="Path to the the positions `.csv` file", type=str)
    parser.add_argument('-fc', '--frame_colname', help="The column name in your positions file corresponding to the frame number", type=str, default='frame')
    parser.add_argument('-xc', '--x_colname', help="The column name in your positions file corresponding to the X coordinate in screen space", type=str, default='left_screen_pos_x')
    parser.add_argument('-yc', '--y_colname', help="The column name in your positions file corresponding to the Y coordinate in screen space", type=str, default='left_screen_pos_y')
    parser.add_argument('-nxc', '--new_x_colname', help="The NEW column name of the re-calibrated x-coord. If an empty string, it will default to `x_colname`", type=str, default='video_x')
    parser.add_argument('-nyc', '--new_y_colname', help="The NEW column name of the re-calibrated y-coord. If an empty string, it will default to `y_colname`", type=str, default='video_y')
    parser.add_argument('-od', '--output_dirname', help="Output directory relative to directory of either the positions filepath or video filepath; a new folder will be generated in the same location as your position/video file", type=str, default='estimations')
    args = parser.parse_args()

    transform_screen_positions(
        args.calibration_filepath,
        args.positions_filepath,
        frame_colname = args.frame_colname,
        x_colname = args.x_colname,
        y_colname = args.y_colname,
        new_x_colname = args.new_x_colname,
        new_y_colname = args.new_y_colname,
        output_dirname = args.output_dirname
    )

