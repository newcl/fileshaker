import os
import sys
import hashlib
import shutil
import json
import datetime
from pathlib import Path
from rich.progress import Progress
from rich.console import Console
from PIL import Image, ExifTags
from mutagen import File as MutagenFile

# Define known file extensions
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.heic', '.webp', '.raw'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.aac', '.flac', '.ogg', '.wma', '.m4a'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}

def compute_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def files_are_identical(file1, file2):
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        while True:
            b1 = f1.read(8192)
            b2 = f2.read(8192)
            if b1 != b2:
                return False
            if not b1:
                return True

def get_creation_date(file_path, file_extension):
    try:
        if file_extension in IMAGE_EXTENSIONS:
            return get_image_date(file_path)
        elif file_extension in AUDIO_EXTENSIONS:
            return get_audio_date(file_path)
        elif file_extension in VIDEO_EXTENSIONS:
            return get_video_date(file_path)
    except Exception:
        pass
    # Fallback to file's modification time
    return datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

def get_image_date(file_path):
    try:
        image = Image.open(file_path)
        exif_data = image._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    return datetime.datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
    except Exception:
        pass
    return datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

def get_audio_date(file_path):
    audio = MutagenFile(file_path)
    if audio:
        if 'TDRC' in audio.tags:
            date = audio.tags['TDRC'].text[0]
            return datetime.datetime.strptime(str(date), '%Y-%m-%d %H:%M:%S')
    return datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

def get_video_date(file_path):
    # Placeholder for video metadata extraction
    return datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

def main(folder1, folder2, target_folder):
    files_seen = {}
    files_copied = {}
    total_size = 0
    all_files = []

    # Collect all files from both folders
    for folder in [folder1, folder2]:
        for root, _, files in os.walk(folder):
            for file in files:
                if file == '.DS_Store':
                    continue
                file_path = os.path.join(root, file)
                all_files.append(file_path)

    console = Console()
    with Progress(console=console) as progress:
        task = progress.add_task("[green]Processing files...", total=len(all_files))

        for file_path in all_files:
            progress.update(task, advance=1)
            file_hash = compute_hash(file_path)
            duplicate_found = False

            if file_hash in files_seen:
                # Compare with all files that have the same hash
                for existing_file in files_seen[file_hash]:
                    if files_are_identical(file_path, existing_file):
                        duplicate_found = True
                        break
                if not duplicate_found:
                    files_seen[file_hash].append(file_path)
            else:
                files_seen[file_hash] = [file_path]

            if duplicate_found:
                continue  # Skip copying if an identical file was found

            file_extension = Path(file_path).suffix.lower()
            creation_date = get_creation_date(file_path, file_extension)
            date_folder = creation_date.strftime('%Y-%m-%d')
            target_path = os.path.join(target_folder, date_folder)

            os.makedirs(target_path, exist_ok=True)
            shutil.copy2(file_path, target_path)

            relative_path = os.path.relpath(target_path, target_folder)
            files_copied[file_path] = os.path.join(relative_path, os.path.basename(file_path))
            total_size += os.path.getsize(file_path)

    # Generate JSON file
    json_file = os.path.join(target_folder, 'file_mapping.json')
    with open(json_file, 'w') as f:
        json.dump(files_copied, f, indent=4)

    # Summary
    console.print(f"\nTotal files copied: {len(files_copied)}")
    console.print(f"Total size copied: {total_size / (1024 * 1024):.2f} MB")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <folder1> <folder2> <target_folder>")
        sys.exit(1)

    folder1 = sys.argv[1]
    folder2 = sys.argv[2]
    target_folder = sys.argv[3]
    main(folder1, folder2, target_folder)
