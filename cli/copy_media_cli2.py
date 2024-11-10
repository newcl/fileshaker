import os
import hashlib
import shutil
from pathlib import Path
import typer
from datetime import datetime
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

def get_creation_month(file_path):
    """Returns the creation month of the file in the format 'YYYY-MM'."""
    try:
        creation_time = os.path.getctime(file_path)
        return datetime.fromtimestamp(creation_time).strftime("%Y-%m")
    except Exception as e:
        console.print(f"[red]Error retrieving creation month for {file_path}: {e}[/red]")
        return "unknown"

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
