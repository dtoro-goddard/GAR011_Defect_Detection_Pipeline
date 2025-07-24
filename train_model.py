#!/usr/bin/env python3
"""
Train Model Script

Trigger model training on a Roboflow dataset using the Roboflow API.
"""
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Train a model on a Roboflow dataset")
    parser.add_argument("--api-key", required=True, help="Roboflow API key")
    parser.add_argument("--project", required=True, help="Roboflow project name")
    parser.add_argument("--workspace", required=True, help="Roboflow workspace name")
    parser.add_argument("--version", type=int, help="Dataset version to train (default: latest)")
    parser.add_argument("--model-type", default="yolov8", help="Model type (e.g., yolov8, yolov5, yolov7, default: yolov8)")
    parser.add_argument("--epochs", type=int, help="Number of epochs (optional)")
    parser.add_argument("--batch-size", type=int, help="Batch size (optional)")
    args = parser.parse_args()

    try:
        from roboflow import Roboflow
    except ImportError:
        print("The 'roboflow' package is required. Install with: pip install roboflow")
        sys.exit(1)

    rf = Roboflow(api_key=args.api_key)
    project = rf.workspace(args.workspace).project(args.project)
    if args.version:
        version = project.version(args.version)
    else:
        version = project.version(project.version())  # latest

    print(f"Triggering training for project '{args.project}', version {version.version}, model type '{args.model_type}'...")
    try:
        # Prepare training parameters
        train_kwargs = {"model_type": args.model_type}
        if args.epochs:
            train_kwargs["epochs"] = args.epochs
        if args.batch_size:
            train_kwargs["batch_size"] = args.batch_size
        # Trigger training
        train_job = version.train(**train_kwargs)
        print("Training started. Monitoring status...")
        # Monitor status if possible
        while True:
            status = train_job.status()
            print(f"Status: {status['status']}")
            if status['status'] in ("succeeded", "failed", "cancelled"):
                print(f"Training finished with status: {status['status']}")
                break
            import time
            time.sleep(10)
        if status['status'] == "succeeded":
            print("Model training complete! You can now deploy or download your model from Roboflow.")
        else:
            print("Model training did not complete successfully.")
    except Exception as e:
        print(f"Error during training: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 