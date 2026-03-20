import os
import pandas as pd
import cv2
import argparse

import helpers as h
import ocr
from classes import Frame

def label_video(
    video_filepath:str,
    positions_filepath:str,
    start_buffer_ms:int = 0,
    frame_colname:str = 'frame',
    x_colname:str = "video_x",
    y_colname:str = "video_y",
    output_dirname:str = 'estimations',
    preview:bool = False,
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="If you have a recording of screen positions (as an `.mp4` file) and the transformed positions of objects shown in that video (as a `.csv` file), then this script produces a re-labeled video. There is no guarantee that the outputted video will be at the same sample rate as the original video.")
    parser.add_argument('video_filepath', help="Filepath to the video file you want to label.", type=str)
    parser.add_argument("positions_filepath", help="File path to the `.csv` file containing coordinates to map to the provided video. Should already be transformed to match video dimensions.", type=str)
    parser.add_argument('-od', '--output_dirname', help="Output directory relative to directory of either the positions filepath or video filepath; a new folder will be generated in the same location as your position/video file", type=str, default='estimations')
    parser.add_argument('-sb', '--start_buffer', help="Buffer time (in seconds) from the video start where we should start processing the video", type=float, default=0.0)
    parser.add_argument('-fc', '--frame_colname', help="The column name in your positions file corresponding to the frame number", type=str, default='frame')
    parser.add_argument('-xc', '--x_colname', help="The column name of the re-calibrated x-coord.", type=str, default='video_x')
    parser.add_argument('-yc', '--y_colname', help="The column name of the re-calibrated y-coord.", type=str, default='video_y')
    parser.add_argument("--preview", help="If set, will preview transformations live", action="store_true")
    parser.add_argument("--verbose", help="When generating videos, do we output messages to the log about progress?", action="store_true")
    args = parser.parse_args()

    label_video(
        args.video_filepath,
        args.position_filepath,
        start_buffer_ms=args.start_buffer * 1000,
        frame_colname = args.frame_colname,
        x_colname = args.x_colname,
        y_colname = args.y_colname,
        output_dirname= args.output_dirname,
        preview = args.preview,
        verbose = args.verbose
    )