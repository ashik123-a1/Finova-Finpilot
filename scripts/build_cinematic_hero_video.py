import os
import sys
import subprocess
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

VIDEO_DIR = r"F:\china project\ashik\video"
OUT_STATIC_DIR = r"F:\china project\src\web\static\videos"
OUT_PUBLIC_DIR = r"F:\china project\public\videos"
FFMPEG = r"C:\Users\ASHIK_CSE\AppData\Local\Programs\Python\Python311\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

os.makedirs(OUT_STATIC_DIR, exist_ok=True)
os.makedirs(OUT_PUBLIC_DIR, exist_ok=True)

vid1_path = os.path.join(VIDEO_DIR, "Finance center creative concept background.mp4")
vid2_path = os.path.join(VIDEO_DIR, "Finance chart stock  - 4k, Free Stock Footage, Copyright Free,  Background, Loop 15-sec.mp4")
vid3_path = os.path.join(VIDEO_DIR, "Stock Market Background Video 4K _ Financial Charts _ Trading Animation _ Business Finance Motion.mp4")

TEMP_DIR = r"C:\Users\ASHIK_CSE\.gemini\antigravity\brain\40635c6d-8320-4cc1-990c-82bc85c90e5c\video_work"
os.makedirs(TEMP_DIR, exist_ok=True)

print("Starting Multi-Video Cinematic Rendering Pipeline...")

# ----------------------------------------------------
# STEP 1: Process Video 1 (Skyscrapers, 4.5s @ 30fps)
# ----------------------------------------------------
clip1_out = os.path.join(TEMP_DIR, "clip1_skyscrapers.mp4")
# Cut 4.5s from t=2.0s to 6.5s
cmd1 = [
    FFMPEG, "-y",
    "-ss", "2.0",
    "-t", "4.5",
    "-i", vid1_path,
    "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30",
    "-c:v", "libx264", "-preset", "fast", "-crf", "20",
    "-pix_fmt", "yuv420p", "-an",
    clip1_out
]
print("Rendering Clip 1 (Skyscrapers)...")
subprocess.run(cmd1, check=True)

# ----------------------------------------------------
# STEP 2: Process Video 2 (3D Monoliths & Financial Trajectories, 6.0s @ 30fps - 100% Clean Footage, No Text)
# ----------------------------------------------------
print("Rendering Clip 2 (Data Monoliths & Trajectories - Clean Cinematic Footage)...")
clip2_clean = os.path.join(TEMP_DIR, "clip2_clean.mp4")
cmd2 = [
    FFMPEG, "-y",
    "-ss", "5.0",
    "-t", "6.0",
    "-i", vid2_path,
    "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30",
    "-c:v", "libx264", "-preset", "fast", "-crf", "20",
    "-pix_fmt", "yuv420p", "-an",
    clip2_clean
]
subprocess.run(cmd2, check=True)


# ----------------------------------------------------
# STEP 3: Process Video 3 (Candlestick Trading with Electric Cyan Color Grade, 4.5s @ 30fps)
# ----------------------------------------------------
print("Rendering Clip 3 (Electric Cyan Color-Graded Candlestick Trading Stream)...")
cap3 = cv2.VideoCapture(vid3_path)
fps3 = cap3.get(cv2.CAP_PROP_FPS)

total_clip3_frames = int(4.5 * 30.0)
start_frame3 = int(2.0 * fps3)
cap3.set(cv2.CAP_PROP_POS_FRAMES, start_frame3)
step_stride3 = fps3 / 30.0

clip3_raw_frames = []
for i in range(total_clip3_frames):
    target_idx = start_frame3 + int(i * step_stride3)
    cap3.set(cv2.CAP_PROP_POS_FRAMES, target_idx)
    ret, frame = cap3.read()
    if not ret:
        break
    if frame.shape[0] != 1080 or frame.shape[1] != 1920:
        frame = cv2.resize(frame, (1920, 1080))

    # Apply Fintech Electric Cyan Color Grading
    b, g, r = cv2.split(frame)
    b_new = cv2.addWeighted(b, 0.45, r, 0.75, 0)
    g_new = cv2.addWeighted(g, 0.80, b, 0.35, 0)
    r_new = cv2.addWeighted(r, 0.15, b, 0.20, 0)
    graded = cv2.merge([b_new, g_new, r_new])

    clip3_raw_frames.append(graded)

cap3.release()

clip3_out = os.path.join(TEMP_DIR, "clip3_candlestick.mp4")
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out_vid3 = cv2.VideoWriter(clip3_out, fourcc, 30.0, (1920, 1080))
for f in clip3_raw_frames:
    out_vid3.write(f)
out_vid3.release()

clip3_clean = os.path.join(TEMP_DIR, "clip3_clean.mp4")
subprocess.run([
    FFMPEG, "-y",
    "-i", clip3_out,
    "-c:v", "libx264", "-preset", "fast", "-crf", "20",
    "-pix_fmt", "yuv420p", "-an",
    clip3_clean
], check=True)

# ----------------------------------------------------
# STEP 4: Seamless Multi-Scene Transition Composition (Clip 1 -> Clip 2 -> Clip 3 -> Loop)
# ----------------------------------------------------
print("Compositing all 3 clips with smooth cinematic crossfades...")
# Clip 1 duration: 4.5s
# Clip 2 duration: 6.0s (offset = 4.5 - 0.5 = 4.0s)
# Clip 3 duration: 4.5s (offset = 4.0 + 6.0 - 0.5 = 9.5s)
# Total sequence = ~13.5s

final_h264_static = os.path.join(OUT_STATIC_DIR, "sme-finance-hero.mp4")
final_webm_static = os.path.join(OUT_STATIC_DIR, "sme-finance-hero.webm")
final_mobile_static = os.path.join(OUT_STATIC_DIR, "sme-finance-hero-mobile.mp4")
final_poster_static = os.path.join(OUT_STATIC_DIR, "sme-finance-hero-poster.jpg")

filter_complex = (
    "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=4.0[v01];"
    "[v01][2:v]xfade=transition=fade:duration=0.5:offset=9.5[vfinal]"
)

composite_cmd = [
    FFMPEG, "-y",
    "-i", clip1_out,
    "-i", clip2_clean,
    "-i", clip3_clean,
    "-filter_complex", filter_complex,
    "-map", "[vfinal]",
    "-c:v", "libx264", "-preset", "slow", "-crf", "22",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an",
    final_h264_static
]
subprocess.run(composite_cmd, check=True)
print("Desktop H.264 generated:", final_h264_static)

# Generate WebM VP9
print("Encoding WebM VP9 variant...")
webm_cmd = [
    FFMPEG, "-y",
    "-i", final_h264_static,
    "-c:v", "libvpx-vp9", "-b:v", "1800k", "-crf", "30", "-an",
    final_webm_static
]
subprocess.run(webm_cmd, check=True)
print("WebM generated:", final_webm_static)

# Generate Mobile 720p / Vertical crop variant
print("Encoding Mobile-optimized variant...")
mobile_cmd = [
    FFMPEG, "-y",
    "-i", final_h264_static,
    "-vf", "scale=-2:720",
    "-c:v", "libx264", "-preset", "fast", "-crf", "24",
    "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an",
    final_mobile_static
]
subprocess.run(mobile_cmd, check=True)
print("Mobile variant generated:", final_mobile_static)

# Generate Poster image (high-res representative frame from Clip 2 with Finova brand)
print("Extracting high-resolution poster frame...")
poster_cmd = [
    FFMPEG, "-y",
    "-ss", "5.5",
    "-i", final_h264_static,
    "-vframes", "1",
    "-q:v", "2",
    final_poster_static
]
subprocess.run(poster_cmd, check=True)
print("Poster image generated:", final_poster_static)

# Mirror to public/videos
for f in ["sme-finance-hero.mp4", "sme-finance-hero.webm", "sme-finance-hero-mobile.mp4", "sme-finance-hero-poster.jpg"]:
    src = os.path.join(OUT_STATIC_DIR, f)
    dst = os.path.join(OUT_PUBLIC_DIR, f)
    import shutil
    shutil.copy2(src, dst)
    print(f"Mirrored {f} to {OUT_PUBLIC_DIR}")

print("ALL ASSETS SUCCESSFULLY GENERATED AND MIRRORED!")
