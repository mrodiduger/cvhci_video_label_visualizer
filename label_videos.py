import cv2
import csv
import os
import argparse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

LABEL_MAP = {
    0: "walk",
    1: "fall",
    2: "fallen",
    3: "sit_down",
    4: "sitting",
    5: "lie_down",
    6: "lying",
    7: "stand_up",
    8: "standing",
    9: "other"
}

def sanitize_filename_component(component):
    """Sanitizes a string component to be file-system friendly."""
    return "".join(c if c.isalnum() or c in (' ', '.', '_') else '_' for c in str(component)).replace(' ', '_')

def process_video(video_path, numeric_label_str, start_sec, end_sec, subject, cam, output_dir, clip_only):
    """
    Processes a single video: reads it, writes a label on frames
    between start_sec and end_sec, and saves it to output_dir.
    If clip_only is True, only the labeled segment is saved.
    """
    try:
        numeric_label = int(numeric_label_str)
        label_to_write = LABEL_MAP.get(numeric_label, f"Unknown_Label_{numeric_label_str}")
        if numeric_label not in LABEL_MAP:
            logging.warning(f"Numeric label {numeric_label_str} not found in LABEL_MAP. Using '{label_to_write}'.")
    except ValueError:
        logging.warning(f"Could not convert label '{numeric_label_str}' to integer. Using it as is or a default.")
        label_to_write = f"Invalid_Label_{numeric_label_str}" # Or handle as you see fit

    if not os.path.exists(video_path):
        logging.error(f"Video file not found: {video_path}")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logging.error(f"Could not open video file: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        logging.error(f"Could not get FPS from video: {video_path}. Assuming 30 FPS.")
        fps = 30 # Default FPS if not readable

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    start_frame = int(start_sec * fps)
    end_frame = int(end_sec * fps)

    original_basename = os.path.splitext(os.path.basename(video_path))[0]
    label_sanitized = sanitize_filename_component(label_to_write) # Use mapped label for filename
    subject_sanitized = sanitize_filename_component(subject)
    cam_sanitized = sanitize_filename_component(cam)
    
    output_filename = f"{original_basename}_{subject_sanitized}_{cam_sanitized}_{label_sanitized}_{start_sec:.1f}s_{end_sec:.1f}s.mp4"
    output_video_path = os.path.join(output_dir, output_filename)

    # Define the codec and create VideoWriter object
    # MP4V is a common codec for .mp4 files. XVID or H264 might also be options.
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

    if not out.isOpened():
        logging.error(f"Could not open video writer for: {output_video_path}")
        cap.release()
        return

    logging.info(f"Processing video: {video_path} -> {output_video_path}")
    if clip_only:
        logging.info(f"Saving clip only for label '{label_to_write}' (from numeric: {numeric_label_str}) from {start_sec}s to {end_sec}s")
    else:
        logging.info(f"Label '{label_to_write}' (from numeric: {numeric_label_str}) from frame {start_frame} ({start_sec}s) to {end_frame} ({end_sec}s)")

    frame_idx = 0
    frames_written = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        is_in_labeled_segment = (start_frame <= frame_idx <= end_frame)

        if is_in_labeled_segment:
            # Add text to the frame if it's in the designated segment
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_position = (50, 50) # Top-left corner
            font_scale = 1
            font_color = (255, 255, 255) # White
            thickness = 2
            line_type = cv2.LINE_AA
            cv2.putText(frame, label_to_write, text_position, font, font_scale, font_color, thickness, line_type)
        
        if clip_only:
            if is_in_labeled_segment:
                out.write(frame)
                frames_written += 1
        else: # Original behavior: write all frames, labeled or not
            out.write(frame)
            frames_written += 1
        
        frame_idx += 1

    cap.release()
    out.release()
    
    if frames_written > 0:
        logging.info(f"Successfully saved video: {output_video_path}")
    else:
        logging.warning(f"No frames were written for {output_video_path}. This might happen if the segment is outside the video's duration or if clip_only is True and the segment is empty.")


def main():
    parser = argparse.ArgumentParser(description="Label videos based on a CSV file.")
    parser.add_argument("csv_file", help="Path to the input CSV file.")
    parser.add_argument("--output_dir", default="output_videos", help="Directory to save processed videos (default: output_videos).")
    parser.add_argument("--video_base_dir", default=None, help="Optional base directory to prepend to video paths in the CSV.")
    parser.add_argument("--video_suffix", default=None, help="Optional suffix to append to video paths (e.g., '.mp4').")
    parser.add_argument("--clip_only", action='store_true', help="If set, only saves the labeled segment as a clip.")
    
    args = parser.parse_args()

    if not os.path.exists(args.csv_file):
        logging.error(f"CSV file not found: {args.csv_file}")
        return

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        logging.info(f"Created output directory: {args.output_dir}")

    try:
        with open(args.csv_file, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)

            for i, row in enumerate(reader):
                try:
                    if len(row) != 6:
                        logging.warning(f"Skipping row {i+1}: Incorrect number of columns ({len(row)} instead of 6). Row content: {row}")
                        continue
                    
                    path_from_csv, label_text_from_csv, start_str, end_str, subject, cam = row
                    
                    video_path_to_process = path_from_csv

                    # Prepend base directory if provided
                    if args.video_base_dir:
                        video_path_to_process = os.path.join(args.video_base_dir, video_path_to_process)
                    
                    # Append suffix if provided
                    if args.video_suffix:
                        suffix_to_add = args.video_suffix
                        if not suffix_to_add.startswith('.') and '.' not in suffix_to_add.split('/')[-1]:
                            suffix_to_add = '.' + suffix_to_add
                        video_path_to_process += suffix_to_add
                    
                    # Ensure the path is normalized
                    video_path_to_process = os.path.normpath(video_path_to_process)

                    start_time = float(start_str)
                    end_time = float(end_str)

                    if start_time < 0 or end_time < 0 or end_time < start_time:
                        logging.warning(f"Skipping row {i+1}: Invalid start/end times ({start_time}s, {end_time}s). Row content: {row}")
                        continue
                        
                    process_video(video_path_to_process, label_text_from_csv, start_time, end_time, subject, cam, args.output_dir, args.clip_only)
                
                except ValueError as e:
                    logging.warning(f"Skipping row {i+1} due to data conversion error: {e}. Row content: {row}")
                except Exception as e:
                    logging.error(f"An unexpected error occurred while processing row {i+1}: {e}. Row content: {row}")

    except FileNotFoundError:
        logging.error(f"CSV file not found: {args.csv_file}")
    except Exception as e:
        logging.error(f"Failed to read or process CSV file: {e}")

if __name__ == "__main__":
    main()
