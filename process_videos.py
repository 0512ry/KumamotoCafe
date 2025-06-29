import subprocess
import os
import whisper
import cv2
import easyocr
import json
import yt_dlp
import argparse

# --- Helper Functions for Video Processing ---

def download_video(url, output_path):
    """Downloads a video from a URL if it doesn't already exist."""
    if os.path.exists(output_path):
        print(f"Video {output_path} already exists. Skipping download.")
        return True

    print(f"Downloading video from {url}...")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'noplaylist': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
        print(f"Video downloaded as: {output_path}")
        return True
    except Exception as e:
        print(f"Error downloading video: {e}")
        return False

def extract_audio(video_path, audio_path):
    """Extracts audio from a video file if it doesn't already exist."""
    if not os.path.exists(video_path):
        print(f"Video file {video_path} not found. Skipping audio extraction.")
        return False
    if os.path.exists(audio_path):
        print(f"Audio file {audio_path} already exists. Skipping extraction.")
        return True

    print(f"Extracting audio from {video_path}...")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-ar", "16000",
            "-ac", "1", "-c:a", "pcm_s16le", audio_path
        ], check=True, capture_output=True)
        print(f"Audio extracted as: {audio_path}")
        return True
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please ensure it's in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio: {e.stderr.decode()}")
    return False

def transcribe_audio(audio_path, transcript_path):
    """Transcribes audio to text using Whisper if it doesn't already exist."""
    if not os.path.exists(audio_path):
        print(f"Audio file {audio_path} not found. Skipping transcription.")
        return False
    if os.path.exists(transcript_path):
        print(f"Transcript file {transcript_path} already exists. Skipping transcription.")
        return True

    print(f"Transcribing audio from {audio_path}...")
    try:
        model = whisper.load_model("small")
        result = model.transcribe(audio_path, language="ja")
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
        print(f"Transcript saved to: {transcript_path}")
        return True
    except Exception as e:
        print(f"Error transcribing audio: {e}")
    return False

def perform_ocr_on_video(video_path, ocr_text_path):
    """Performs OCR on video frames if it hasn't been done already."""
    if not os.path.exists(video_path):
        print(f"Video file {video_path} not found. Skipping OCR.")
        return False
    if os.path.exists(ocr_text_path):
        print(f"OCR file {ocr_text_path} already exists. Skipping OCR.")
        return True

    print(f"Performing OCR on frames from {video_path}...")
    try:
        reader = easyocr.Reader(['ja', 'en'])
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return False
        
        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        ocr_results = []
        frame_interval = int(frame_rate) if frame_rate > 0 else 1

        current_frame_index = 0
        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_index)
            ret, frame = cap.read()
            if not ret:
                break

            result = reader.readtext(frame, detail=0)
            if result:
                ocr_results.extend(result)

            current_frame_index += frame_interval
        
        cap.release()

        if ocr_results:
            unique_ocr_results = list(set(ocr_results))
            with open(ocr_text_path, "w", encoding="utf-8") as f:
                f.write("\n".join(unique_ocr_results))
            print(f"OCR results saved to: {ocr_text_path}")
        else:
            print("No text detected in video frames.")
        return True
    except Exception as e:
        print(f"Error during OCR: {e}")
    return False

def extract_keyframes(video_path, output_dir, image_prefix):
    """Extracts keyframes based on scene changes, up to 20 images."""
    if not os.path.exists(video_path):
        print(f"Video file {video_path} not found. Skipping keyframe extraction.")
        return

    # Clear old images first
    for i in range(1, 21):
        old_img_path = f"{image_prefix}cafe_image_{i}.jpg"
        if os.path.exists(old_img_path):
            os.remove(old_img_path)

    print(f"Extracting key frames from {video_path}...")
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return

        frame_rate = cap.get(cv2.CAP_PROP_FPS) or 30
        prev_frame = None
        frame_count = 0
        extracted_images_count = 0
        last_saved_frame_time = -2.0
        min_time_between_saves = 1.0
        scene_change_threshold = 1.5

        while extracted_images_count < 20:
            ret, frame = cap.read()
            if not ret: break

            current_time = frame_count / frame_rate
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

            if prev_frame is not None:
                frame_delta = cv2.absdiff(prev_frame, gray_frame)
                thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
                diff_percentage = (cv2.countNonZero(thresh) / (frame.shape[0] * frame.shape[1])) * 100

                if diff_percentage > scene_change_threshold and (current_time - last_saved_frame_time) > min_time_between_saves:
                    extracted_images_count += 1
                    output_filename = f"{image_prefix}cafe_image_{extracted_images_count}.jpg"
                    cv2.imwrite(output_filename, frame)
                    print(f"Scene change detected. Saved {output_filename}")
                    last_saved_frame_time = current_time
            
            prev_frame = gray_frame
            frame_count += 1
        
        cap.release()
        print(f"Finished extracting {extracted_images_count} images.")

    except Exception as e:
        print(f"An error occurred during key frame extraction: {e}")

def extract_tiktok_metadata(tiktok_url, output_dir, description_path, comments_path):
    """Extracts TikTok video description and comments using yt-dlp."""
    print(f"Extracting metadata from {tiktok_url}...")
    ydl_opts = {
        'skip_download': True, # Only extract info, don't download video again
        'writesubtitles': False, # We use Whisper for transcription
        'writeinfojson': True, # Write video info to JSON
        'noplaylist': True,
        'quiet': True, # Suppress console output from yt-dlp
        'force_generic_extractor': True, # Force generic extractor for TikTok
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(tiktok_url, download=False)
            
            # Save description
            description = info_dict.get('description', '')
            with open(description_path, "w", encoding="utf-8") as f:
                f.write(description)
            print(f"Description saved to: {description_path}")

            # Save comments (if available)
            comments = info_dict.get('comments', [])
            if comments:
                with open(comments_path, "w", encoding="utf-8") as f:
                    json.dump(comments, f, ensure_ascii=False, indent=2)
                print(f"Comments saved to: {comments_path}")
            else:
                print("No comments found or extracted.")

    except Exception as e:
        print(f"Error extracting TikTok metadata: {e}")

# --- Main Orchestration ---

def process_cafe(cafe_details):
    """Runs the full processing pipeline for a single cafe."""
    cafe_id = cafe_details['id']
    output_dir = cafe_id
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n--- Processing: {cafe_details['name']} (Output to ./{output_dir}) ---")

    # Define file paths
    video_path = os.path.join(output_dir, f"{cafe_id}_tiktok_video.mp4")
    audio_path = os.path.join(output_dir, f"{cafe_id}_tiktok_audio.wav")
    transcript_path = os.path.join(output_dir, f"{cafe_id}_tiktok_transcript.txt")
    ocr_text_path = os.path.join(output_dir, f"{cafe_id}_tiktok_ocr_text.txt")
    description_path = os.path.join(output_dir, f"{cafe_id}_tiktok_description.txt")
    comments_path = os.path.join(output_dir, f"{cafe_id}_tiktok_comments.json")
    image_prefix = os.path.join(output_dir, f"{cafe_id}_")

    # Run processing steps
    if download_video(cafe_details['tiktok_url'], video_path):
        # extract_tiktok_metadata(cafe_details['tiktok_url'], output_dir, description_path, comments_path) # Temporarily disabled
        if extract_audio(video_path, audio_path):
            transcribe_audio(audio_path, transcript_path)
        perform_ocr_on_video(video_path, ocr_text_path)
        extract_keyframes(video_path, output_dir, image_prefix)

def main():
    parser = argparse.ArgumentParser(description="Process TikTok videos and manage cafe data.")
    parser.add_argument("--url", help="TikTok video URL to process as a new cafe.")
    args = parser.parse_args()

    try:
        with open("cafes.json", "r", encoding="utf-8") as f:
            cafes_data = json.load(f)
    except FileNotFoundError:
        print("Error: cafes.json not found. Creating a new one.")
        cafes_data = []
    except json.JSONDecodeError:
        print("Error: Could not decode cafes.json. Please check its format. Starting with empty data.")
        cafes_data = []

    if args.url:
        # Process a new URL
        existing_ids = [int(c['id'].replace('cafe', '')) for c in cafes_data if c['id'].startswith('cafe') and c['id'].replace('cafe', '').isdigit()]
        new_id_num = 1
        if existing_ids: 
            new_id_num = max(existing_ids) + 1
        new_cafe_id = f"cafe{new_id_num}"

        new_cafe_entry = {
            "id": new_cafe_id,
            "name": f"新しいカフェ ({new_id_num})", # Placeholder name
            "tiktok_url": args.url,
            "address": "不明",
            "description": "",
            "info": {},
            "menu_summary": "",
            "links": {}
        }
        print(f"Adding new cafe: {new_cafe_entry['name']} with ID {new_cafe_id}")
        
        # Process video first to get OCR and transcript for search query
        process_cafe(new_cafe_entry) # This will create the cafe folder and files

        # Read OCR and transcript for search query
        ocr_text = ""
        transcript_text = ""
        ocr_file_path = os.path.join(new_cafe_id, f"{new_cafe_id}_tiktok_ocr_text.txt")
        transcript_file_path = os.path.join(new_cafe_id, f"{new_cafe_id}_tiktok_transcript.txt")

        if os.path.exists(ocr_file_path):
            with open(ocr_file_path, "r", encoding="utf-8") as f:
                ocr_text = f.read().strip()
        if os.path.exists(transcript_file_path):
            with open(transcript_file_path, "r", encoding="utf-8") as f:
                transcript_text = f.read().strip()
        
        # Form a more concise search query
        query_parts = []
        if ocr_text:
            query_parts.extend(ocr_text.split('\n')[:3]) # Take first 3 lines
        if transcript_text:
            query_parts.extend(transcript_text.split('\n')[:3]) # Take first 3 lines
        
        base_query = " ".join([p.strip() for p in query_parts if p.strip()])
        
        search_query = f"{base_query} 熊本カフェ".strip()
        if not search_query: # Fallback if no text extracted
            search_query = "熊本カフェ"

        # Save the search query to a file
        search_query_file_path = os.path.join(new_cafe_id, f"{new_cafe_id}_search_query.txt")
        with open(search_query_file_path, "w", encoding="utf-8") as f:
            f.write(search_query)
        print(f"Search query saved to: {search_query_file_path}")

        # Add the new cafe entry with placeholder info to cafes.json
        cafes_data.append(new_cafe_entry)
        with open("cafes.json", "w", encoding="utf-8") as f:
            json.dump(cafes_data, f, ensure_ascii=False, indent=2)
        print("cafes.json updated with new cafe (placeholder info).")

        # Output structured request for the agent to process
        print(f"AGENT_REQUEST_GOOGLE_MAPS_INFO: {json.dumps({'cafe_id': new_cafe_id, 'search_query': search_query})})")
    else:
        # Process all existing cafes
        for cafe in cafes_data:
            process_cafe(cafe)

    # Automatically call generate_html.py after video processing
    print("\n--- Video processing complete. Generating HTML... ---")
    try:
        # Use the virtual environment's python to run generate_html.py
        subprocess.run([
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv_tiktok", "Scripts", "python.exe"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "generate_html.py")
        ], check=True)
        print("HTML generation triggered successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error triggering HTML generation: {e}")
    except FileNotFoundError:
        print("Error: generate_html.py or venv_tiktok python executable not found. Please check paths.")

if __name__ == "__main__":
    main()