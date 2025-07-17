#!/usr/bin/env python3
"""
Roboflow Photo Uploader

A Python script that uses the Roboflow SDK to upload photos to your Roboflow project.
Supports batch uploading, different upload modes, and comprehensive error handling.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional
import logging
from roboflow import Roboflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('roboflow_upload.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RoboflowUploader:
    """A class to handle photo uploads to Roboflow."""
    
    def __init__(self, api_key: str, project_name: str, workspace_name: str):
        """
        Initialize the Roboflow uploader.
        
        Args:
            api_key: Your Roboflow API key
            project_name: Name of your Roboflow project
            workspace_name: Name of your Roboflow workspace
        """
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
        """
        Upload a single photo to Roboflow.
        
        Args:
            image_path: Path to the image file
            split: Dataset split (train, valid, test)
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return False
            
            # Get the filename without extension
            filename = Path(image_path).stem
            
            logger.info(f"Uploading {image_path} to {split} split...")
            
            # Upload the image
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
    
    def upload_batch_photos(self, image_dir: str, split: str = "train", 
                          file_extensions: List[str] = None) -> dict:
        """
        Upload multiple photos from a directory.
        
        Args:
            image_dir: Directory containing images
            split: Dataset split (train, valid, test)
            file_extensions: List of file extensions to upload (default: ['.jpg', '.jpeg', '.png'])
            
        Returns:
            dict: Upload statistics
        """
        if file_extensions is None:
            file_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
        if not os.path.exists(image_dir):
            logger.error(f"Directory not found: {image_dir}")
            return {"success": 0, "failed": 0, "total": 0}
        
        # Find all image files
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
        """
        Get information about the current project.
        
        Returns:
            dict: Project information
        """
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


def main():
    """Main function to handle command line arguments and execute uploads."""
    parser = argparse.ArgumentParser(
        description="Upload photos to Roboflow using the Roboflow SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload a single image
  python roboflow_uploader.py --api-key YOUR_API_KEY --project my-project --workspace my-workspace --image path/to/image.jpg
  
  # Upload all images from a directory
  python roboflow_uploader.py --api-key YOUR_API_KEY --project my-project --workspace my-workspace --directory path/to/images --split train
  
  # Upload with custom file extensions
  python roboflow_uploader.py --api-key YOUR_API_KEY --project my-project --workspace my-workspace --directory path/to/images --extensions .jpg .png .tiff
        """
    )
    
    parser.add_argument("--api-key", required=True, help="Your Roboflow API key")
    parser.add_argument("--project", required=True, help="Name of your Roboflow project")
    parser.add_argument("--workspace", required=True, help="Name of your Roboflow workspace")
    parser.add_argument("--image", help="Path to a single image file to upload")
    parser.add_argument("--directory", help="Directory containing images to upload")
    parser.add_argument("--split", default="train", choices=["train", "valid", "test"], 
                       help="Dataset split (default: train)")
    parser.add_argument("--extensions", nargs="+", 
                       default=[".jpg", ".jpeg", ".png", ".bmp", ".tiff"],
                       help="File extensions to upload (default: .jpg .jpeg .png .bmp .tiff)")
    parser.add_argument("--info", action="store_true", help="Display project information")
    
    args = parser.parse_args()
    
    try:
        # Initialize uploader
        uploader = RoboflowUploader(args.api_key, args.project, args.workspace)
        
        # Display project info if requested
        if args.info:
            info = uploader.get_project_info()
            print("\nProject Information:")
            for key, value in info.items():
                print(f"  {key}: {value}")
            print()
        
        # Upload single image
        if args.image:
            success = uploader.upload_single_photo(args.image, args.split)
            if success:
                print(f"Successfully uploaded {args.image}")
            else:
                print(f"Failed to upload {args.image}")
                sys.exit(1)
        
        # Upload batch from directory
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
            parser.print_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nUpload interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 