#!/usr/bin/env python3
"""
Example usage of the RoboflowUploader class

This script demonstrates how to use the RoboflowUploader class programmatically
instead of using the command line interface.
"""

import os
from roboflow_uploader import RoboflowUploader


def main():
    """Example usage of the RoboflowUploader class."""
    
    # Configuration - replace with your actual values
    API_KEY = "your_roboflow_api_key_here"
    PROJECT_NAME = "your-project-name"
    WORKSPACE_NAME = "your-workspace-name"
    
    # Example image paths - replace with actual paths
    SINGLE_IMAGE_PATH = "path/to/your/image.jpg"
    IMAGE_DIRECTORY = "path/to/your/images/folder"
    
    try:
        # Initialize the uploader
        print("Initializing Roboflow uploader...")
        uploader = RoboflowUploader(API_KEY, PROJECT_NAME, WORKSPACE_NAME)
        
        # Display project information
        print("\n=== Project Information ===")
        info = uploader.get_project_info()
        for key, value in info.items():
            print(f"{key}: {value}")
        
        # Example 1: Upload a single image
        print("\n=== Uploading Single Image ===")
        if os.path.exists(SINGLE_IMAGE_PATH):
            success = uploader.upload_single_photo(SINGLE_IMAGE_PATH, split="train")
            if success:
                print(f"Successfully uploaded {SINGLE_IMAGE_PATH}")
            else:
                print(f"Failed to upload {SINGLE_IMAGE_PATH}")
        else:
            print(f"Image file not found: {SINGLE_IMAGE_PATH}")
        
        # Example 2: Upload multiple images from a directory
        print("\n=== Uploading Batch Images ===")
        if os.path.exists(IMAGE_DIRECTORY):
            # Upload with default extensions
            stats = uploader.upload_batch_photos(IMAGE_DIRECTORY, split="train")
            print(f"📊 Batch upload completed:")
            print(f"  Total files: {stats['total']}")
            print(f"  Successful: {stats['success']}")
            print(f"  Failed: {stats['failed']}")
            
            # Upload with custom extensions
            custom_extensions = ['.jpg', '.png']
            stats_custom = uploader.upload_batch_photos(
                IMAGE_DIRECTORY, 
                split="valid", 
                file_extensions=custom_extensions
            )
            print(f"Custom extensions upload completed:")
            print(f"  Total files: {stats_custom['total']}")
            print(f"  Successful: {stats_custom['success']}")
            print(f"  Failed: {stats_custom['failed']}")
        else:
            print(f"Directory not found: {IMAGE_DIRECTORY}")
        
        print("\n=== Example completed successfully ===")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 