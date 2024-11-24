from PIL import Image
import pyheif
import imagehash
from pathlib import Path
import shutil
import os
import subprocess
from datetime import datetime
from typing import Optional, List, Tuple
import typer
from threading import Thread
from queue import Queue
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn
from rich.logging import RichHandler
import logging
import json

app = typer.Typer()
console = Console()

# Configure rich logging
logging.basicConfig(
    level="INFO", format="%(message)s", handlers=[RichHandler(console=console)]
)
logger = logging.getLogger("rich")

def get_image_hash(image_path: Path) -> Optional[Tuple[imagehash.ImageHash, Path]]:
    try:
        if image_path.suffix.lower() == ".heic":
            heif_file = pyheif.read(image_path)
            image = Image.frombytes(
                heif_file.mode, heif_file.size, heif_file.data, "raw", heif_file.mode
            )
        else:
            image = Image.open(image_path)

        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        img_hash = imagehash.phash(image)
        return img_hash, image_path
    except Exception as e:
        logger.error(f"[bold red]Error processing image {image_path}: {e}")
        return None

def get_creation_date(file_path: Path) -> str:
    try:
        # Run exiftool and retrieve metadata
        result = subprocess.run(
            [
                "exiftool",
                "-s",
                "-s",
                "-s",
                "-DateTimeOriginal",
                "-CreateDate",
                "-MediaCreateDate",
                str(file_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse the result to find the date
        date_str = result.stdout.strip()
        if date_str:
            return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S").strftime("%Y-%m")

    except Exception as e:
        logger.warning(f"[yellow]Metadata extraction failed for {file_path}: {e}")

    # Fallback to file modification time
    creation_time = datetime.fromtimestamp(file_path.stat().st_mtime)
    return creation_time.strftime("%Y-%m")

def process_images(image_paths: List[Path], num_threads: int = 8) -> List[Tuple[imagehash.ImageHash, Path]]:
    def worker():
        while True:
            image_path = q.get()
            if image_path is None:
                break
            result = get_image_hash(image_path)
            if result:
                hashes.append(result)
            progress.update(task, advance=1)
            q.task_done()

    q = Queue()
    threads = []
    hashes = []
    total_images = len(image_paths)

    with Progress(SpinnerColumn(), "[progress.description]{task.description}", BarColumn(), console=console) as progress:
        task = progress.add_task("Hashing images...", total=total_images)

        for _ in range(num_threads):
            t = Thread(target=worker)
            t.start()
            threads.append(t)

        for image_path in image_paths:
            q.put(image_path)

        # Block until all tasks are done
        q.join()

        # Stop workers
        for _ in range(num_threads):
            q.put(None)
        for t in threads:
            t.join()

    return hashes

def group_similar_images(hashes: List[Tuple[imagehash.ImageHash, Path]], hash_threshold: int) -> List[List[Tuple[imagehash.ImageHash, Path]]]:
    # Convert hashes to integers for sorting
    hashes_int = [(int(str(h[0]), 16), h[1]) for h in hashes]
    # Sort by hash value
    hashes_int.sort(key=lambda x: x[0])

    groups = []
    current_group = []
    n = len(hashes_int)

    for i in range(n):
        img_hash, img_path = hashes_int[i]
        if not current_group:
            current_group.append((img_hash, img_path))
        else:
            prev_hash = current_group[-1][0]
            hamming_distance = bin(img_hash ^ prev_hash).count('1')
            if hamming_distance <= hash_threshold:
                current_group.append((img_hash, img_path))
            else:
                groups.append(current_group)
                current_group = [(img_hash, img_path)]

    if current_group:
        groups.append(current_group)

    return groups

def copy_files(
    source: Path,
    target: Path,
    image_groups: List[List[Tuple[int, Path]]],
    non_image_files: List[Path],
):
    # Copy non-image files
    with Progress(console=console) as progress:
        task = progress.add_task("[green]Copying non-image files...", total=len(non_image_files))
        for file in non_image_files:
            date_folder = target / get_creation_date(file)
            date_folder.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, date_folder / file.name)
            logger.info(f"Copied non-image file {file} to {date_folder}")
            progress.update(task, advance=1)

    # Copy images and collect similar image groups
    total_groups = len(image_groups)
    similar_images_data = []
    with Progress(console=console) as progress:
        task = progress.add_task("[green]Copying image files...", total=total_groups)
        for group in image_groups:
            files = [Path(p[1]) for p in group]
            largest_file = max(files, key=lambda f: f.stat().st_size)
            date_folder = target / get_creation_date(largest_file)
            date_folder.mkdir(parents=True, exist_ok=True)
            shutil.copy2(largest_file, date_folder / largest_file.name)
            logger.info(f"Copied largest image {largest_file} to {date_folder}")

            # Collect similar images data
            similar_files = [str(file) for file in files if file != largest_file]
            if similar_files:
                group_data = {
                    "largest_image": str(largest_file),
                    "similar_images": similar_files
                }
                similar_images_data.append(group_data)

            progress.update(task, advance=1)

    # Write the similar images data to a JSON file
    json_file_path = target / "similar_images.json"
    with open(json_file_path, "w") as json_file:
        json.dump(similar_images_data, json_file, indent=4)
    logger.info(f"Generated JSON file with similar image groups at {json_file_path}")

@app.command()
def main(source_folder: str, target_folder: str, hash_threshold: int = 5, num_threads: int = 8):
    source = Path(source_folder)
    target = Path(target_folder)
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp", ".heic"]

    # Collect all files in the source directory
    all_files = list(source.rglob("*"))
    all_files = [f for f in all_files if f.is_file()]

    logger.info(f"Found {len(all_files)} files to process.")

    # Separate image files and non-image files
    image_files = [f for f in all_files if f.suffix.lower() in image_extensions]
    non_image_files = [f for f in all_files if f.suffix.lower() not in image_extensions]

    logger.info(f"Processing {len(image_files)} image files and {len(non_image_files)} non-image files.")

    # Step 1: Compute hashes using multithreading
    image_hashes = process_images(image_files, num_threads=num_threads)

    # Step 2: Group similar images
    image_groups = group_similar_images(image_hashes, hash_threshold)

    logger.info(f"Found {len(image_groups)} groups of similar images.")

    # Step 3: Copy files and generate JSON
    copy_files(source, target, image_groups, non_image_files)

if __name__ == "__main__":
    app()
