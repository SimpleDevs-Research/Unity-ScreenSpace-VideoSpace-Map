import subprocess
import os
import argparse
import cv2

# -------- CONFIG --------
ANGLE_DEG = 21
K1 = -0.48
K2 = 0.2
CX = 0.57
CY = 0.51

FILL_COLOR = "black"

# ------------------------

def run_ffmpeg(input_file, vf_chain, output_file):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_file,
        "-vf", vf_chain,
        output_file
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

def get_image_size(path):
    img = cv2.imread(path)
    h, w = img.shape[:2]
    return w, h

def build_rotate(angle_deg):
    angle_expr = f"{angle_deg}*(PI/180)"
    return (
        f"rotate={angle_expr}:"
        f"ow=rotw({angle_expr}):"
        f"oh=roth({angle_expr}):"
        f"fillcolor={FILL_COLOR}"
    )

def build_center_crop(orig_w, orig_h):
    return f"crop={orig_w}:{orig_h}:(in_w-{orig_w})/2:(in_h-{orig_h})/2"

def build_lens(k1, k2):
    return f"lenscorrection=cx={CX}:cy={CY}:k1={k1}:k2={k2}"


def pipeline(input_img, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # ---- Step 1: Forward transforms ----

    # A: Distortion → Rotation
    a1 = os.path.join(output_dir, "A_distort_then_rotate.png")
    vf_a1 = f"{build_lens(K1, K2)},{build_rotate(ANGLE_DEG)}"
    run_ffmpeg(input_img, vf_a1, a1)

    # B: Rotation → Distortion
    b1 = os.path.join(output_dir, "B_rotate_then_distort.png")
    vf_b1 = f"{build_rotate(ANGLE_DEG)},{build_lens(K1, K2)}"
    run_ffmpeg(input_img, vf_b1, b1)

    # ---- Step 2: Reverse transforms ----

    orig_w, orig_h = get_image_size(input_img)
    crop_filter = build_center_crop(orig_w, orig_h)

    # Reverse A: undo rotation → undo distortion
    a2 = os.path.join(output_dir, "A_recovered.png")
    vf_a2 = (
        f"{build_rotate(-ANGLE_DEG)},"
        f"{build_lens(-K1, -K2)},"
        f"{crop_filter}"
    )
    run_ffmpeg(a1, vf_a2, a2)

    # Reverse B: undo distortion → undo rotation
    b2 = os.path.join(output_dir, "B_recovered.png")
    vf_b2 = (
        f"{build_lens(-K1, -K2)},"
        f"{build_rotate(-ANGLE_DEG)},"
        f"{crop_filter}"
    )
    run_ffmpeg(b1, vf_b2, b2)

    print("\nDone. Outputs saved in:", output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Provided an input image, perform a series of distortions and un-distortions to validate the idea of data information loss.")
    parser.add_argument('input_image', help="Filepath to the input image to be tested", type=str)
    parser.add_argument('output_dir', help="where the output images should be saved.", type=str)
    args = parser.parse_args()

    pipeline(args.input_image, args.output_dir)