#!/usr/bin/env python3
"""
ML Pipeline CLI

A command-line tool for managing datasets and models with Roboflow and SharePoint integration.
"""

import argparse
import sys
import logging
from roboflow import Roboflow
from pathlib import Path
import os
import getpass
import json

# Import RoboflowUploader from roboflow_uploader.py (move the class definition here in the next step)
# from roboflow_uploader import RoboflowUploader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_pipeline_cli.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path.home() / ".ml_pipeline_cli" / "config.json"


def save_config(api_key, project=None, workspace=None):
    config_dir = CONFIG_PATH.parent
    config_dir.mkdir(parents=True, exist_ok=True)
    config = {"api_key": api_key}
    if project:
        config["project"] = project
    if workspace:
        config["workspace"] = workspace
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)
    os.chmod(CONFIG_PATH, 0o600)


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

# --- RoboflowUploader class (moved from roboflow_uploader.py) ---
class RoboflowUploader:
    # ... existing code from roboflow_uploader.py ...
    def __init__(self, api_key: str, project_name: str, workspace_name: str):
        self.api_key = api_key
        self.project_name = project_name
        self.workspace_name = workspace_name
        try:
            self.rf = Roboflow(api_key=api_key)
            self.project = self.rf.workspace(workspace_name).project(project_name)
            logger.info(f"Successfully connected to project: {project_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Roboflow connection: {e}")
            raise
    def upload_single_photo(self, image_path: str, split: str = "train") -> bool:
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return False
            filename = Path(image_path).stem
            logger.info(f"Uploading {image_path} to {split} split...")
            self.project.upload(
                image_path=image_path,
                num_retry_uploads=3,
                split=split
            )
            logger.info(f"Successfully uploaded {filename} to {split} split")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {image_path}: {e}")
            return False
    def upload_batch_photos(self, image_dir: str, split: str = "train", file_extensions=None) -> dict:
        if file_extensions is None:
            file_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        if not os.path.exists(image_dir):
            logger.error(f"Directory not found: {image_dir}")
            return {"success": 0, "failed": 0, "total": 0}
        image_files = []
        for ext in file_extensions:
            image_files.extend(Path(image_dir).glob(f"*{ext}"))
            image_files.extend(Path(image_dir).glob(f"*{ext.upper()}"))
        if not image_files:
            logger.warning(f"No image files found in {image_dir}")
            return {"success": 0, "failed": 0, "total": 0}
        logger.info(f"Found {len(image_files)} images to upload")
        success_count = 0
        failed_count = 0
        for image_file in image_files:
            if self.upload_single_photo(str(image_file), split):
                success_count += 1
            else:
                failed_count += 1
        stats = {
            "success": success_count,
            "failed": failed_count,
            "total": len(image_files)
        }
        logger.info(f"Batch upload completed: {success_count} successful, {failed_count} failed")
        return stats
    def get_project_info(self) -> dict:
        try:
            info = {
                "name": self.project.name,
                "type": self.project.type,
                "version": self.project.version,
                "workspace": self.workspace_name
            }
            return info
        except Exception as e:
            logger.error(f"Failed to get project info: {e}")
            return {}

# --- CLI setup ---
def main():
    parser = argparse.ArgumentParser(description="ML Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Upload subcommand
    upload_parser = subparsers.add_parser("upload", help="Upload images to Roboflow")
    upload_parser.add_argument("--api-key")
    upload_parser.add_argument("--project")
    upload_parser.add_argument("--workspace")
    upload_parser.add_argument("--image", help="Path to a single image file to upload")
    upload_parser.add_argument("--directory", help="Directory containing images to upload")
    upload_parser.add_argument("--split", default="train", choices=["train", "valid", "test"])
    upload_parser.add_argument("--extensions", nargs="+", default=[".jpg", ".jpeg", ".png", ".bmp", ".tiff"])
    upload_parser.add_argument("--info", action="store_true", help="Display project information")

    # Download subcommand
    download_parser = subparsers.add_parser("download", help="Download datasets from Roboflow")
    download_parser.add_argument("--output-dir", default="./data", help="Directory to save the dataset")
    download_parser.add_argument("--format", default="yolov8", help="Dataset format (e.g., yolov8, coco, voc)")
    download_parser.add_argument("--version", type=int, help="Dataset version number (default: latest)")

    # Infer subcommand
    infer_parser = subparsers.add_parser("infer", help="Run model inference on images")
    infer_parser.add_argument("--image", help="Path to a single image file to run inference on")
    infer_parser.add_argument("--directory", help="Directory containing images to run inference on")
    infer_parser.add_argument("--model-id", help="Roboflow model id (project/version), e.g. my-project/1")
    infer_parser.add_argument("--confidence", type=float, default=0.4, help="Confidence threshold (0-1, default: 0.4)")
    infer_parser.add_argument("--output-dir", default="./inference_results", help="Directory to save inference results as JSON")

    # Sync subcommand
    sync_parser = subparsers.add_parser("sync", help="Sync local folders with SharePoint and Roboflow")
    sync_parser.add_argument("--sharepoint-site", help="SharePoint site URL")
    sync_parser.add_argument("--sharepoint-folder", help="SharePoint document library/folder (e.g. 'Shared Documents/Folder')")
    sync_parser.add_argument("--local-folder", help="Local folder to sync")
    sync_parser.add_argument("--direction", choices=["to-local", "to-sharepoint", "both"], default="both", help="Sync direction (default: both)")
    sync_parser.add_argument("--client-id", help="Azure AD App client ID (optional)")
    sync_parser.add_argument("--client-secret", help="Azure AD App client secret (optional)")
    sync_parser.add_argument("--username", help="SharePoint username (optional)")
    sync_parser.add_argument("--password", help="SharePoint password (optional)")

    # Sync-all subcommand
    sync_all_parser = subparsers.add_parser("sync-all", help="Sync local dataset folders (train/valid/test) with both SharePoint and Roboflow")
    sync_all_parser.add_argument("--local-root", required=True, help="Local root folder containing train/valid/test folders")
    sync_all_parser.add_argument("--sharepoint-site", required=True, help="SharePoint site URL")
    sync_all_parser.add_argument("--sharepoint-folder", required=True, help="SharePoint document library/folder (e.g. 'Shared Documents/Folder')")
    sync_all_parser.add_argument("--project", help="Roboflow project name")
    sync_all_parser.add_argument("--workspace", help="Roboflow workspace name")
    sync_all_parser.add_argument("--api-key", help="Roboflow API key")
    sync_all_parser.add_argument("--client-id", help="Azure AD App client ID (optional)")
    sync_all_parser.add_argument("--client-secret", help="Azure AD App client secret (optional)")
    sync_all_parser.add_argument("--username", help="SharePoint username (optional)")
    sync_all_parser.add_argument("--password", help="SharePoint password (optional)")

    # Login subcommand
    login_parser = subparsers.add_parser("login", help="Authenticate with Roboflow and store API key")
    login_parser.add_argument("--api-key", help="Roboflow API key (if not provided, will prompt)")
    login_parser.add_argument("--project", help="Default project name (optional)")
    login_parser.add_argument("--workspace", help="Default workspace name (optional)")

    # Train subcommand (placeholder)
    train_parser = subparsers.add_parser("train", help="Train a model on a dataset")
    # TODO: Add arguments

    # Video-infer subcommand (placeholder)
    video_infer_parser = subparsers.add_parser("video-infer", help="Run model on video stream from camera")
    # TODO: Add arguments

    # Video-capture subcommand (placeholder)
    video_capture_parser = subparsers.add_parser("video-capture", help="Capture video from camera to dataset folder")
    # TODO: Add arguments

    args = parser.parse_args()

    if args.command == "login":
        api_key = args.api_key or getpass.getpass("Enter your Roboflow API key: ")
        project = args.project
        workspace = args.workspace
        save_config(api_key, project, workspace)
        print(f"Roboflow credentials saved to {CONFIG_PATH}")
        sys.exit(0)

    # Load config for other commands
    config = load_config()
    api_key = (
        args.api_key or
        os.environ.get("ROBOFLOW_API_KEY") or
        config.get("api_key")
    )
    project = (
        getattr(args, "project", None) or
        os.environ.get("ROBOFLOW_PROJECT") or
        config.get("project")
    )
    workspace = (
        getattr(args, "workspace", None) or
        os.environ.get("ROBOFLOW_WORKSPACE") or
        config.get("workspace")
    )

    if args.command == "upload":
        if not api_key or not project or not workspace:
            print("API key, project, and workspace are required. Use the 'login' command or provide them via arguments or environment variables.")
            sys.exit(1)
        uploader = RoboflowUploader(api_key, project, workspace)
        if args.info:
            info = uploader.get_project_info()
            print("\nProject Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
            print()
        if args.image:
            success = uploader.upload_single_photo(args.image, args.split)
            if success:
                print(f"Successfully uploaded {args.image}")
            else:
                print(f"Failed to upload {args.image}")
                sys.exit(1)
        elif args.directory:
            stats = uploader.upload_batch_photos(args.directory, args.split, args.extensions)
            print(f"\nUpload Summary:")
            print(f"  Total files: {stats['total']}")
            print(f"  Successful: {stats['success']}")
            print(f"  Failed: {stats['failed']}")
            if stats['failed'] > 0:
                sys.exit(1)
        else:
            print("Please specify either --image or --directory")
            sys.exit(1)
    elif args.command == "download":
        if not api_key or not project or not workspace:
            print("API key, project, and workspace are required. Use the 'login' command or provide them via arguments or environment variables.")
            sys.exit(1)
        try:
            rf = Roboflow(api_key=api_key)
            proj = rf.workspace(workspace).project(project)
            if args.version:
                version = proj.version(args.version)
            else:
                version = proj.version(proj.version())  # latest version
            print(f"Downloading dataset version {version.version} in format '{args.format}'...")
            dataset_dir = version.download(args.format, location=args.output_dir)
            print(f"Dataset downloaded to: {dataset_dir}")
            # Check for train/valid/test folders
            for split in ["train", "valid", "test"]:
                split_path = Path(dataset_dir) / split
                if split_path.exists():
                    print(f"  Found split folder: {split_path}")
                else:
                    print(f"  Warning: Split folder not found: {split_path}")
            print("Download complete.")
        except Exception as e:
            print(f"Error downloading dataset: {e}")
            sys.exit(1)
    elif args.command == "infer":
        try:
            from inference import get_model
            import json
            import glob
            from pathlib import Path
            import os

            model_id = args.model_id
            if not model_id:
                # Try to infer model_id from project/version
                if not project or not config.get("project") or not config.get("project"):
                    print("You must provide --model-id or have project/version in config.")
                    sys.exit(1)
                # Use latest version if not specified
                rf = Roboflow(api_key=api_key)
                proj = rf.workspace(workspace).project(project)
                version_num = proj.version()  # latest
                model_id = f"{project}/{version_num}"

            model = get_model(model_id=model_id, api_key=api_key)
            Path(args.output_dir).mkdir(parents=True, exist_ok=True)

            def run_and_save(img_path):
                results = model.infer(img_path, confidence=args.confidence)
                out_path = Path(args.output_dir) / (Path(img_path).stem + "_predictions.json")
                with open(out_path, "w") as f:
                    json.dump(results, f, indent=2)
                print(f"Inference results saved to {out_path}")
                return results

            if args.image:
                if not os.path.exists(args.image):
                    print(f"Image file not found: {args.image}")
                    sys.exit(1)
                run_and_save(args.image)
            elif args.directory:
                exts = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
                images = []
                for ext in exts:
                    images.extend(glob.glob(str(Path(args.directory) / f"*{ext}")))
                    images.extend(glob.glob(str(Path(args.directory) / f"*{ext.upper()}")))
                if not images:
                    print(f"No images found in {args.directory}")
                    sys.exit(1)
                print(f"Found {len(images)} images. Running inference...")
                for img_path in images:
                    run_and_save(img_path)
                print("Batch inference complete.")
            else:
                print("Please specify either --image or --directory for inference.")
                sys.exit(1)
        except ImportError:
            print("The 'inference' package is required. Install with: pip install inference")
            sys.exit(1)
        except Exception as e:
            print(f"Error during inference: {e}")
            sys.exit(1)
    elif args.command == "sync":
        try:
            from sharepoint_sync import SharePointSync
            # Validate required arguments
            if not args.sharepoint_site or not args.sharepoint_folder or not args.local_folder:
                print("--sharepoint-site, --sharepoint-folder, and --local-folder are required.")
                sys.exit(1)
            syncer = SharePointSync(
                site_url=args.sharepoint_site,
                sharepoint_folder=args.sharepoint_folder,
                local_folder=args.local_folder,
                direction=args.direction,
                client_id=args.client_id,
                client_secret=args.client_secret,
                username=args.username,
                password=args.password
            )
            syncer.authenticate()
            syncer.sync()
        except ImportError:
            print("The 'office365-rest-python-client' package is required. Install with: pip install Office365-REST-Python-Client")
            sys.exit(1)
        except Exception as e:
            print(f"SharePoint sync error: {e}")
            sys.exit(1)
    elif args.command == "sync-all":
        try:
            from sharepoint_sync import SharePointSync
            # Import RoboflowUploader from this file
            RoboflowUploader = globals().get('RoboflowUploader')
            if RoboflowUploader is None:
                # If not in globals, define a fallback import (for future refactor)
                from roboflow import Roboflow
                class RoboflowUploader:
                    def __init__(self, api_key, project_name, workspace_name):
                        self.api_key = api_key
                        self.project_name = project_name
                        self.workspace_name = workspace_name
                        self.rf = Roboflow(api_key=api_key)
                        self.project = self.rf.workspace(workspace_name).project(project_name)
                    def upload_batch_photos(self, image_dir, split, file_extensions=None):
                        if file_extensions is None:
                            file_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
                        from pathlib import Path
                        import os
                        image_files = []
                        for ext in file_extensions:
                            image_files.extend(Path(image_dir).glob(f"*{ext}"))
                            image_files.extend(Path(image_dir).glob(f"*{ext.upper()}"))
                        success_count = 0
                        failed_count = 0
                        for image_file in image_files:
                            try:
                                self.project.upload(
                                    image_path=str(image_file),
                                    num_retry_uploads=3,
                                    split=split
                                )
                                success_count += 1
                            except Exception:
                                failed_count += 1
                        return {"success": success_count, "failed": failed_count, "total": len(image_files)}
            # Validate required arguments
            for arg in [args.local_root, args.sharepoint_site, args.sharepoint_folder, args.project, args.workspace, args.api_key]:
                if not arg:
                    print("--local-root, --sharepoint-site, --sharepoint-folder, --project, --workspace, and --api-key are required.")
                    sys.exit(1)
            splits = ["train", "valid", "test"]
            summary = {}
            for split in splits:
                local_split = os.path.join(args.local_root, split)
                sp_split = f"{args.sharepoint_folder}/{split}"
                # Ensure local split folder exists
                Path(local_split).mkdir(parents=True, exist_ok=True)
                # Sync local <-> SharePoint for this split
                print(f"\nSyncing {split} folder between local and SharePoint...")
                sp_sync = SharePointSync(
                    site_url=args.sharepoint_site,
                    sharepoint_folder=sp_split,
                    local_folder=local_split,
                    direction="both",
                    client_id=args.client_id,
                    client_secret=args.client_secret,
                    username=args.username,
                    password=args.password
                )
                sp_sync.authenticate()
                sp_sync.sync()
                # Upload local images to Roboflow for this split
                print(f"Uploading local {split} images to Roboflow...")
                uploader = RoboflowUploader(args.api_key, args.project, args.workspace)
                stats = uploader.upload_batch_photos(local_split, split)
                summary[split] = stats
            print("\nSync Summary:")
            for split, stats in summary.items():
                print(f"  {split}: {stats['success']} uploaded, {stats['failed']} failed, {stats['total']} total")
            print("\nSync-all complete.")
        except ImportError:
            print("The 'office365-rest-python-client' and 'roboflow' packages are required. Install with: pip install Office365-REST-Python-Client roboflow")
            sys.exit(1)
        except Exception as e:
            print(f"Sync-all error: {e}")
            sys.exit(1)
    elif args.command == "train":
        print("Training functionality not yet implemented.")
    elif args.command == "video-infer":
        print("Video inference functionality not yet implemented.")
    elif args.command == "video-capture":
        print("Video capture functionality not yet implemented.")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 