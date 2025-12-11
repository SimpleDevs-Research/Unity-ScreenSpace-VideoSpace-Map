import cv2

# Initialize variables
drawing = False     # True while mouse is down
ix, iy = -1, -1     # Initial mouse down position
ex, ey = -1, -1     # Current mouse move position
x1, x2, y1, y2 = -1,-1,-1,-1
roi_selected = False
roi = None          # The selected region
frame_for_roi = None
display_frame = None

# Bounding Box drawer
def draw_rectangle(event, x, y, flags, param):
    global ix, iy, ex, ey, x1, y1, x2, y2, drawing, roi_selected, display_frame, roi

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        ex, ey = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            ex, ey = x, y
            # Show live-updating rectangle
            temp = frame_for_roi.copy()
            cv2.rectangle(temp, (ix, iy), (ex, ey), (0, 255, 0), 2)
            display_frame = temp

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        ex, ey = x, y
        roi_selected = True

        # Ensure coordinates are sorted
        x1, x2 = min(ix, ex), max(ix, ex)
        y1, y2 = min(iy, ey), max(iy, ey)

        roi = frame_for_roi[y1:y2, x1:x2].copy()
        print(f"ROI: ({x1},{y1}) - ({x2},{y2}) w/ shape ", roi.shape)

        # Draw the final rectangle
        temp = frame_for_roi.copy()
        cv2.rectangle(temp, (x1, y1), (x2, y2), (0, 255, 0), 2)
        display_frame = temp

# ------------------------------------------------------------
# ESTIMATIONS: Given a trial with a Transformer established, map video frames to Unity frames.
# Then remap positional data from VR screenspace to video space. This outputs a new video with
# The positions marked and a CSV with the re-positioned entities.
# ------------------------------------------------------------

def frame_count_bounding_box(video_filepath:str):
    global frame_for_roi, display_frame, roi, x1, y1, x2, y2

    # Initialize a frame capture, get the first frame
    cap = cv2.VideoCapture(video_filepath)
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Failed to read first frame.")
    frame_for_roi = frame.copy()
    display_frame = frame.copy()
    cv2.namedWindow("Select ROI")
    cv2.setMouseCallback("Select ROI", draw_rectangle)

    # ROI Selection Loop
    while True:
        cv2.imshow("Select ROI", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # ENTER key
            break
        if key == 27:  # ESC key cancels
            roi = None
            break
    cv2.waitKey(1)  # 1 ms delay
    cv2.destroyWindow("Select ROI")

    if roi is None:
        print("No ROI selected.")
    else:
        print("ROI stored! shape =", roi.shape)

    return (x1,y1), (x2,y2)