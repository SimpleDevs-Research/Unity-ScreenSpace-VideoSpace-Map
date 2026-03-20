import os
import cv2
import numpy as np
import argparse

def extract_frame(
    input_img_path:str,
    output_name_append:str = "-cropped",
    color_tolerance = 10
):
    # Helper: color comparison
    def is_background(pixel, edge_pixels, tol):
        return np.any(np.all(np.abs(edge_pixels - pixel) <= tol, axis=1))

    # Estimate background color
    def estimate_background(img, x, y, w, h):
        edges = []
        edges.append(img[y, x:x+w])
        edges.append(img[y+h-1, x:x+w])
        edges.append(img[y:y+h, x])
        edges.append(img[y:y+h, x+w-1])
        edges = np.concatenate(edges, axis=0)
        return edges
    
    # Shrink bounding box inward
    def shrink_bbox(img, x, y, w, h, bg_color, tol):
        left = x
        right = x + w - 1
        top = y
        bottom = y + h - 1
        changed = True

        while changed:
            changed = False
            # shrink top
            while top <= bottom:
                row = img[top, left:right+1]
                if all(is_background(p, bg_color, tol) for p in row):
                    top += 1
                    changed = True
                else:
                    break
            # shrink bottom
            while bottom >= top:
                row = img[bottom, left:right+1]
                if all(is_background(p, bg_color, tol) for p in row):
                    bottom -= 1
                    changed = True
                else:
                    break
            # shrink left
            while left <= right:
                col = img[top:bottom+1, left]
                if all(is_background(p, bg_color, tol) for p in col):
                    left += 1
                    changed = True
                else:
                    break
            # shrink right
            while right >= left:
                col = img[top:bottom+1, right]
                if all(is_background(p, bg_color, tol) for p in col):
                    right -= 1
                    changed = True
                else:
                    break
        # Return new bounding box coords
        return left, top, right, bottom
    
    # Main operations
    img = cv2.imread(input_img_path)
    if img is None:
        print("Failed to load image")
        return
    # Let user select ROI
    roi = cv2.selectROI("Select Bounding Box", img, showCrosshair=True)
    cv2.destroyAllWindows()
    x, y, w, h = map(int, roi)
    # Estimate background color
    bg_color = estimate_background(img, x, y, w, h)
    print("Estimated background color:", bg_color)
    # Shrink bounding box
    left, top, right, bottom = shrink_bbox(
        img, x, y, w, h, bg_color, color_tolerance
    )
    # Crop result
    cropped = img[top:bottom+1, left:right+1]
    # Save
    outdir, fpath = os.path.split(input_img_path)
    fname, fext = os.path.splitext(fpath)
    output_path = os.path.join(outdir, fname+output_name_append+fext)
    cv2.imwrite(output_path, cropped)
    print("Saved cropped image to:", output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Given a single frame, draw a bounding box, and produce a subsample that isn't just the background.")
    parser.add_argument("input_img_filepath", help="The filepath to the image to crop.", type=str)
    parser.add_argument("-o", "--output_name_append",  help="The text to append to the filename when extracting and saving the cropped image.", type=str, default="-cropped")
    parser.add_argument("-ct", "--color_tolerance", help="Color tolerance as a buffer for the background color", type=int, default=10)
    args = parser.parse_args()

    extract_frame(
        args.input_img_filepath,
        output_name_append = args.output_name_append,
        color_tolerance = args.color_tolerance
    )