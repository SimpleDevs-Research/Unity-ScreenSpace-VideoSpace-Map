import os
import cv2
import argparse

def extract_frames(
    video_path:str,
    output_ext:str="png"
):
    root_dir, fname = os.path.split(video_path)
    fname, _ = os.path.splitext(fname)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    current_frame = 0

    window_name = "Frame Selector"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    def on_trackbar(val):
        nonlocal current_frame
        current_frame = val
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

    # Create trackbar
    cv2.createTrackbar("Frame", window_name, 0, total_frames - 1, on_trackbar)

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
        ret, frame = cap.read()

        if not ret:
            print("Error: Could not read frame.")
            break

        display_frame = frame.copy()
        cv2.putText(display_frame, f"Frame: {current_frame}/{total_frames}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2)

        cv2.imshow(window_name, display_frame)

        key = cv2.waitKey(30) & 0xFF

        if key == ord('q') or key == 27:  # ESC
            break
        elif key == ord('a'):  # Step backward
            current_frame = max(0, current_frame - 1)
            cv2.setTrackbarPos("Frame", window_name, current_frame)
        elif key == ord('d'):  # Step forward
            current_frame = min(total_frames - 1, current_frame + 1)
            cv2.setTrackbarPos("Frame", window_name, current_frame)
        elif key in (10, 13):  # Enter to save frame (Linux/Mac = 10, Windows = 13)
            filename = f"{fname}_{current_frame}.{output_ext}"
            filepath = os.path.join(root_dir, filename)
            cv2.imwrite(filepath, frame)
            print(f"Saved: {filepath}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Given a single frame, draw a bounding box, and produce a subsample that isn't just the background.")
    parser.add_argument("video_path", help="The filepath to the video to extract frames from.", type=str)
    parser.add_argument("-oe", "--output_ext", help="The output image filetype ('png','jpg','svg').", type=str, choices=['png','jpg','svg'], default='png')
    args = parser.parse_args()

    extract_frames(
        args.video_path,
        output_ext = args.output_ext
    )