#!/usr/bin/env python3
"""
Video Stream Inference Script

Continuously runs a Roboflow model on a video stream from a camera, displaying annotated results in real time.
"""
import argparse
import cv2
import sys

def main():
    parser = argparse.ArgumentParser(description="Run Roboflow model on video stream from camera (real-time inference)")
    parser.add_argument("--model-id", required=True, help="Roboflow model id (project/version), e.g. my-project/1")
    parser.add_argument("--api-key", required=True, help="Roboflow API key")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--confidence", type=float, default=0.4, help="Confidence threshold (0-1, default: 0.4)")
    parser.add_argument("--output", help="Optional: path to save annotated video")
    args = parser.parse_args()

    try:
        from inference import get_model
        import supervision as sv
    except ImportError:
        print("The 'inference' and 'supervision' packages are required. Install with: pip install inference supervision")
        sys.exit(1)

    model = get_model(model_id=args.model_id, api_key=args.api_key)
    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        print(f"Failed to open camera {args.camera}")
        sys.exit(1)

    writer = None
    if args.output:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(args.output, fourcc, fps, (width, height))

    print("Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame from camera.")
            break
        # Run inference
        results = model.infer(frame, confidence=args.confidence)[0]
        detections = sv.Detections.from_inference(results)
        # Annotate frame
        box_annotator = sv.BoxAnnotator()
        label_annotator = sv.LabelAnnotator()
        labels = [p.class_name for p in results['predictions']] if 'predictions' in results else []
        annotated = box_annotator.annotate(scene=frame, detections=detections)
        annotated = label_annotator.annotate(scene=annotated, detections=detections, labels=labels)
        # Show
        cv2.imshow("Roboflow Inference", annotated)
        if writer:
            writer.write(annotated)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 