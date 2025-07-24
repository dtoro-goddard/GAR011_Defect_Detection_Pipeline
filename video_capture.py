#!/usr/bin/env python3
"""
Video Capture Script

Capture video from a camera and save frames to a dataset split folder (train/valid/test).
"""
import argparse
import cv2
import os
from pathlib import Path
import sys

def main():
    parser = argparse.ArgumentParser(description="Capture video from camera and save frames to dataset folder")
    parser.add_argument("--output-folder", required=True, help="Root dataset folder (will save to <output-folder>/<split>/)")
    parser.add_argument("--split", required=True, choices=["train", "valid", "test"], help="Dataset split to save frames to")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--frame-interval", type=int, default=5, help="Save every Nth frame (default: 5)")
    parser.add_argument("--duration", type=int, help="Optional: duration to capture in seconds (default: unlimited)")
    args = parser.parse_args()

    split_dir = Path(args.output_folder) / args.split
    split_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Failed to open camera {args.camera}")
        sys.exit(1)

    print(f"Capturing from camera {args.camera}. Press 'q' to stop.")
    print(f"Saving every {args.frame_interval}th frame to {split_dir}")
    frame_count = 0
    saved_count = 0
    start_time = cv2.getTickCount() / cv2.getTickFrequency()
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame from camera.")
            break
        frame_count += 1
        if frame_count % args.frame_interval == 0:
            filename = split_dir / f"frame_{frame_count:06d}.jpg"
            cv2.imwrite(str(filename), frame)
            saved_count += 1
            print(f"Saved {filename}")
        cv2.imshow("Video Capture", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Capture stopped by user.")
            break
        if args.duration:
            elapsed = (cv2.getTickCount() / cv2.getTickFrequency()) - start_time
            if elapsed >= args.duration:
                print(f"Reached duration limit: {args.duration} seconds.")
                break
    cap.release()
    cv2.destroyAllWindows()
    print(f"\nCapture complete. {saved_count} frames saved to {split_dir}.")

if __name__ == "__main__":
    main() 