# Video Labeler

This script processes videos based on information provided in a CSV file. It writes a specified label onto video frames between a given start and end time, and saves the result as a new video file.

## Prerequisites

- Python 3.x
- OpenCV for Python

## Installation

1.  **Clone the repository (or download the files):**
    ```bash
    # If this were a git repository:
    # git clone <repository_url>
    # cd cvhci_video_labeler
    ```
    For now, ensure you have `label_videos.py`, `requirements.txt`, and optionally `sample_data.csv` in a directory (e.g., `/home/rodi/cvhci_video_labeler`).

2.  **Install dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

## CSV File Format

The input CSV file **should not have a header row**. Each line must contain the following columns in order:

1.  `path_to_video`: Relative path to the source video file (without extension if `--video_suffix` is used). This path will be combined with `--video_base_dir` if provided.
2.  `label`: The numeric label (0-9) for the action. This will be mapped to a string (e.g., "fall", "walk").
3.  `start`: The start time (in seconds) for displaying the label. Can be a float (e.g., `1.5`).
4.  `end`: The end time (in seconds) for displaying the label. Can be a float (e.g., `3.0`).
5.  `subject`: An identifier for the subject in the video (used for output filename).
6.  `cam`: An identifier for the camera used (used for output filename).

**Example (`sample_data.csv`):**
```csv
caucafall/video/backwards/FallBackwardsS6,8,0.0,2.22,6,1
caucafall/video/side/FallLeftS1,1,0.91,2.99,1,1
```
**Note:** The paths in the CSV are relative. Use `--video_base_dir` to specify the root directory for these paths and `--video_suffix` to add file extensions if they are not in the CSV.

## Usage

Run the script from the command line:

```bash
python label_videos.py <csv_file_path> [options]
```

**Arguments:**

-   `csv_file` (required, positional): Path to the input CSV file.
-   `--output_dir` (optional): Directory where labeled videos will be saved. Defaults to `output_videos` in the current working directory. The script will create this directory if it doesn't exist.
-   `--video_base_dir` (optional): Base directory to prepend to the video paths found in the CSV file.
-   `--video_suffix` (optional): Suffix to append to video paths from the CSV (e.g., `.mp4`, `.avi`). If the suffix doesn't start with a `.` and doesn't look like an extension, a `.` will be prepended.
-   `--clip_only` (optional, flag): If set, only the labeled segment (from `start` to `end` seconds) is saved as a new video clip. Otherwise, the entire video is saved with the label applied during the specified segment.

**Example:**

```bash
python label_videos.py sample_data.csv --video_base_dir /path/to/my/videos --video_suffix .mp4 --output_dir processed_vids --clip_only
```

This command will:
1. Read `sample_data.csv`.
2. For each entry, construct the full video path by prepending `/path/to/my/videos/` and appending `.mp4` to the path from the CSV.
3. Process the video, applying the mapped string label.
4. Save only the segment between `start` and `end` seconds as a new clip into the `processed_vids` directory.

## Customization

-   **Text Appearance**: The font, size, color, and position of the label text are currently hardcoded in the `process_video` function in `label_videos.py`. You can modify these parameters directly in the script if needed:
    ```python
    # Inside process_video function:
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_position = (50, 50) # (x, y) from top-left
    font_scale = 1
    font_color = (255, 255, 255) # White in BGR
    thickness = 2
    line_type = cv2.LINE_AA
    cv2.putText(frame, label, text_position, font, font_scale, font_color, thickness, line_type)
    ```
-   **Video Codec**: The output video codec is set to `mp4v`. If you encounter issues or prefer a different codec (e.g., `XVID`, `avc1` for H.264), you can change the `fourcc` code in `label_videos.py`:
    ```python
    # Inside process_video function:
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    # e.g., for XVID: fourcc = cv2.VideoWriter_fourcc(*'XVID')
    ```

## Logging

The script uses Python's `logging` module to output information, warnings, and errors to the console. This helps in tracking progress and diagnosing issues.
