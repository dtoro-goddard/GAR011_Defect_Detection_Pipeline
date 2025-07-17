# Roboflow Photo Uploader

A Python program that uses the Roboflow SDK to upload photos to your Roboflow projects. This tool supports both single image uploads and batch uploads from directories, with comprehensive error handling and logging.

## Features

- **Single Image Upload**: Upload individual photos to your Roboflow project
- **Batch Upload**: Upload multiple images from a directory at once
- **Dataset Splits**: Support for train, validation, and test splits

## Prerequisites

- Python 3.7 or higher
- A Roboflow account and API key
- A Roboflow project created in your workspace

## Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd ml_pipeline_sdk
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get your Roboflow API key**
   - Go to [Roboflow](https://roboflow.com)
   - Sign in to your account
   - Navigate to your workspace settings
   - Copy your API key

## Usage

### Basic Commands

#### Upload a Single Image
```bash
python roboflow_uploader.py \
  --api-key YOUR_API_KEY \
  --project your-project-name \
  --workspace your-workspace-name \
  --image path/to/your/image.jpg
```

#### Upload All Images from a Directory
```bash
python roboflow_uploader.py \
  --api-key YOUR_API_KEY \
  --project your-project-name \
  --workspace your-workspace-name \
  --directory path/to/images/folder \
  --split train
```

#### Upload with Custom File Extensions
```bash
python roboflow_uploader.py \
  --api-key YOUR_API_KEY \
  --project your-project-name \
  --workspace your-workspace-name \
  --directory path/to/images/folder \
  --extensions .jpg .png .tiff
```

#### Display Project Information
```bash
python roboflow_uploader.py \
  --api-key YOUR_API_KEY \
  --project your-project-name \
  --workspace your-workspace-name \
  --info
```

### Command Line Arguments

| Argument | Required | Description | Default |
|----------|----------|-------------|---------|
| `--api-key` | Yes | Your Roboflow API key | - |
| `--project` | Yes | Name of your Roboflow project | - |
| `--workspace` | Yes | Name of your Roboflow workspace | - |
| `--image` | No* | Path to a single image file | - |
| `--directory` | No* | Directory containing images to upload | - |
| `--split` | No | Dataset split (train/valid/test) | train |
| `--extensions` | No | File extensions to upload | .jpg .jpeg .png .bmp .tiff |
| `--info` | No | Display project information | False |

*Either `--image` or `--directory` must be specified (unless using `--info`)

### Examples

#### Example 1: Upload Training Images
```bash
python roboflow_uploader.py \
  --api-key rf_abc123def456 \
  --project "my-object-detection-project" \
  --workspace "my-workspace" \
  --directory "./training_images" \
  --split train
```

#### Example 2: Upload Validation Images
```bash
python roboflow_uploader.py \
  --api-key rf_abc123def456 \
  --project "my-object-detection-project" \
  --workspace "my-workspace" \
  --directory "./validation_images" \
  --split valid
```

#### Example 3: Upload Only JPG and PNG Files
```bash
python roboflow_uploader.py \
  --api-key rf_abc123def456 \
  --project "my-object-detection-project" \
  --workspace "my-workspace" \
  --directory "./images" \
  --extensions .jpg .png
```

#### Example 4: Upload a Single Test Image
```bash
python roboflow_uploader.py \
  --api-key rf_abc123def456 \
  --project "my-object-detection-project" \
  --workspace "my-workspace" \
  --image "./test_image.jpg" \
  --split test
```

## Output and Logging

The program provides comprehensive feedback:

### Console Output
- Real-time upload progress
- Success/failure messages for each file
- Summary statistics for batch uploads
- Error messages for failed uploads

### Log File
All activities are logged to `roboflow_upload.log` in the current directory, including:
- Connection status
- Upload attempts and results
- Error details
- Timestamps for all operations

### Example Output
```
2024-01-15 10:30:15 - INFO - Successfully connected to project: my-object-detection-project
2024-01-15 10:30:15 - INFO - Found 25 images to upload
2024-01-15 10:30:16 - INFO - Uploading ./images/cat1.jpg to train split...
2024-01-15 10:30:17 - INFO - Successfully uploaded cat1 to train split
...

Upload Summary:
  Total files: 25
  Successful: 25
  Failed: 0
```

## Error Handling

The program includes robust error handling:

- **Network Issues**: Automatic retry with exponential backoff
- **Invalid Files**: Skips corrupted or unsupported files
- **API Errors**: Detailed error messages for troubleshooting
- **Missing Files/Directories**: Clear error messages for missing paths
- **Authentication Errors**: Helpful messages for API key issues

## Supported File Formats

The program supports the following image formats:
- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff)

## Environment Variables (Optional)

You can set environment variables to avoid passing API keys on the command line:

```bash
export ROBOFLOW_API_KEY="your_api_key_here"
export ROBOFLOW_PROJECT="your_project_name"
export ROBOFLOW_WORKSPACE="your_workspace_name"
```

Then use the script without the `--api-key`, `--project`, and `--workspace` arguments.

## Troubleshooting

### Common Issues

1. **"Failed to initialize Roboflow connection"**
   - Check your API key is correct
   - Verify your project and workspace names
   - Ensure you have internet connectivity

2. **"Image file not found"**
   - Verify the file path is correct
   - Check file permissions
   - Ensure the file exists

3. **"No image files found in directory"**
   - Check the directory path
   - Verify files have supported extensions
   - Check file permissions

4. **Upload failures**
   - Check your Roboflow project settings
   - Verify you have upload permissions
   - Check file size limits

### Getting Help

- Check the log file `roboflow_upload.log` for detailed error information
- Verify your Roboflow project settings in the web interface
- Ensure your API key has the necessary permissions

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool.

## License

This project is open source and available under the MIT License.

## Support

For Roboflow-specific issues, visit the [Roboflow Documentation](https://docs.roboflow.com/) or [Roboflow Support](https://roboflow.com/support). # GAR011_Defect_Detection_Pipeline
