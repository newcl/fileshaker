import os
import hashlib
import shutil
from pathlib import Path
import typer
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from mutagen import File as MutagenFile
import ffmpeg
from rich.console import Console
from rich.progress import track

app = typer.Typer()
console = Console()

# Comprehensive set of media extensions
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg",
    ".heic", ".heif", ".raw", ".cr2", ".nef", ".orf", ".arw", ".dng",
    ".psd", ".ai", ".eps", ".ico", ".tga", ".jfif", ".jp2", ".avif"
}
VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv", ".webm", ".m4v"
}
AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".wma", ".aac", ".flac", ".ogg", ".m4a", ".aiff", ".amr"
}

ALL_MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

def hash_file(file_path):
    """Returns the SHA-256 hash of the file's contents."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_image_creation_time(file_path):
    """Extracts the creation time from image metadata."""
    try:
        image = Image.open(file_path)
        exif_data = image._getexif()
        if exif_data:
            for tag, value in exif_data.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == 'DateTimeOriginal':  # Standard tag for image creation time
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
        return None
    except Exception as e:
        console.print(f"[red]Error extracting image metadata: {e}[/red]")
        return None

def get_audio_creation_time(file_path):
    """Extracts the creation time from audio metadata."""
    try:
        audio = MutagenFile(file_path)
        if audio and 'TDRC' in audio.tags:
            return audio.tags['TDRC'].text[0].datetime
        return None
    except Exception as e:
        console.print(f"[red]Error extracting audio metadata: {e}[/red]")
        return None

def get_video_creation_time(file_path):
    """Extracts the creation time from video metadata using ffmpeg."""
    try:
        probe = ffmpeg.probe(file_path)
        for stream in probe['streams']:
            if 'tags' in stream and 'creation_time' in stream['tags']:
                return datetime.fromisoformat(stream['tags']['creation_time'].replace('Z', ''))
        return None
    except ffmpeg.Error as e:
        console.print(f"[red]Error extracting video metadata: {e}[/red]")
        return None

def get_creation_month(file_path):
    """Determines the creation month from a file's metadata."""
    ext = os.path.splitext(file_path)[1].lower()

    creation_time = None
    if ext in IMAGE_EXTENSIONS:
        creation_time = get_image_creation_time(file_path)
    elif ext in AUDIO_EXTENSIONS:
        creation_time = get_audio_creation_time(file_path)
    elif ext in VIDEO_EXTENSIONS:
        creation_time = get_video_creation_time(file_path)

    if creation_time:
        return creation_time.strftime("%Y-%m")

    # Fall back to file system creation time if no metadata is available
    creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
    return creation_time.strftime("%Y-%m")

@app.command()
def copy_media(source_folder: str, target_folder: str):
    """
    Copies all image, video, and audio files from the source folder to the target folder without duplication.
    Files are organized into subfolders named after their creation month (e.g., '2023-05').
    
    Parameters:
    source_folder: str - The source folder to scan for media files.
    target_folder: str - The target folder to copy media files into.
    """
    source_folder = Path(source_folder)
    target_folder = Path(target_folder)

    if not source_folder.is_dir():
        console.print("[bold red]Source folder is not a valid directory.[/bold red]")
        raise typer.Exit()

    # Create the target folder if it doesn't exist
    target_folder.mkdir(parents=True, exist_ok=True)

    seen_hashes = {}
    copied_files_count = 0

    console.print(f"[cyan]Scanning folder: [bold]{source_folder}[/bold][/cyan]")

    # Iterate over all files in the source folder and subfolders
    for root, _, files in os.walk(source_folder):
        for file in track(files, description="Processing files..."):
            file_path = Path(root) / file
            if file_path.suffix.lower() in ALL_MEDIA_EXTENSIONS and file_path.is_file():
                file_hash = hash_file(file_path)

                if file_hash not in seen_hashes:
                    # Get the creation month and create the corresponding subfolder
                    creation_month = get_creation_month(file_path)
                    month_folder = target_folder / creation_month
                    month_folder.mkdir(parents=True, exist_ok=True)

                    # Copy the file to the target folder with a subfolder for its creation month
                    target_path = month_folder / file_path.name

                    # Ensure the target path does not already exist
                    if target_path.exists():
                        # Rename the file to avoid overwriting
                        target_path = month_folder / f"{file_path.stem}_{file_hash[:8]}{file_path.suffix}"

                    shutil.copy2(file_path, target_path)
                    seen_hashes[file_hash] = target_path
                    copied_files_count += 1
                else:
                    console.print(f"[yellow]Duplicate found, skipping: {file_path}[/yellow]")

    console.print(f"[green]Copy operation complete. {copied_files_count} unique media file(s) copied.[/green]")

if __name__ == "__main__":
    app()
