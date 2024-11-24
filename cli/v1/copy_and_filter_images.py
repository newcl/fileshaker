import os
import shutil
import typer
from pathlib import Path
from imagededup.methods import PHash
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.progress import Progress, track

app = typer.Typer()
console = Console()

def get_image_size(file_path):
    """Returns the size (in bytes) of the image."""
    return os.path.getsize(file_path)

def calculate_hamming_distance(hash1, hash2):
    """Calculates the Hamming distance between two perceptual hashes."""
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

def hash_image(image_path, phasher):
    """Calculates and returns the perceptual hash of an image."""
    try:
        hash_value = phasher.encode_image(image_file=str(image_path))
        return str(image_path), hash_value
    except Exception as e:
        console.print(f"[red]Error hashing image {image_path}: {e}[/red]")
        return str(image_path), None

@app.command()
def copy_and_filter(
    source_folder: str,
    target_folder: str,
    threshold: int = 10,
    max_threads: int = 4
):
    """
    Copies files from the source folder to the target folder.
    Detects similar images based on perceptual hash and only keeps the largest one.
    Copies all other file types as they are.

    Parameters:
    source_folder: str - Path to the source folder.
    target_folder: str - Path to the target folder.
    threshold: int - Hamming distance threshold for determining similarity.
    max_threads: int - Number of threads to use for concurrent processing.
    """
    source_path = Path(source_folder)
    target_path = Path(target_folder)

    if not source_path.is_dir():
        console.print("[bold red]The provided source path is not a valid directory.[/bold red]")
        raise typer.Exit()

    target_path.mkdir(parents=True, exist_ok=True)

    # Initialize PHash for finding similar images
    phasher = PHash()
    image_hashes = {}

    # Step 1: Calculate hashes for all images in the source folder using multi-threading
    with Progress(console=console) as progress:
        task = progress.add_task("Hashing images...", total=len(list(source_path.rglob('*'))))
        
        with ThreadPoolExecutor(max_threads) as executor:
            futures = {executor.submit(hash_image, image_path, phasher): image_path for image_path in source_path.rglob('*') if image_path.is_file() and image_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic']}
            for future in as_completed(futures):
                image_path, hash_value = future.result()
                if hash_value:
                    image_hashes[image_path] = hash_value
                progress.update(task, advance=1)

    # Step 2: Group similar images based on the Hamming distance
    console.print("[cyan]Grouping similar images...[/cyan]")
    similar_groups = defaultdict(list)
    processed_images = set()

    for img1, hash1 in image_hashes.items():
        if img1 not in processed_images:
            similar_groups[img1].append(img1)
            processed_images.add(img1)
            for img2, hash2 in image_hashes.items():
                if img1 != img2 and img2 not in processed_images:
                    distance = calculate_hamming_distance(hash1, hash2)
                    if distance < threshold:
                        similar_groups[img1].append(img2)
                        processed_images.add(img2)

    # Step 3: Identify the largest image in each group
    console.print("[cyan]Selecting the largest image in each group...[/cyan]")
    largest_images = {}
    excluded_duplicates_count = 0

    for base_image, image_list in similar_groups.items():
        if len(image_list) > 1:
            excluded_duplicates_count += len(image_list) - 1

        max_size = 0
        largest_image = None

        for image_path in image_list:
            image_size = get_image_size(image_path)
            if image_size > max_size:
                max_size = image_size
                largest_image = image_path

        if largest_image:
            largest_images[largest_image] = max_size

    # Step 4: Copy the largest images and all non-image files
    console.print("[cyan]Copying files to the target folder...[/cyan]")
    copied_files_count = 0

    with Progress(console=console) as progress:
        copy_task = progress.add_task("Copying files...", total=len(list(source_path.rglob('*'))))
        
        with ThreadPoolExecutor(max_threads) as executor:
            futures = []
            for item in source_path.rglob('*'):
                target_item_path = target_path / item.relative_to(source_path)

                if item.is_file():
                    if str(item) in largest_images:
                        if not target_item_path.exists():
                            target_item_path.parent.mkdir(parents=True, exist_ok=True)
                            futures.append(executor.submit(shutil.copy2, item, target_item_path))
                            copied_files_count += 1
                    elif not any(item.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic']):
                        target_item_path.parent.mkdir(parents=True, exist_ok=True)
                        futures.append(executor.submit(shutil.copy2, item, target_item_path))
                        copied_files_count += 1

            for _ in as_completed(futures):
                progress.update(copy_task, advance=1)

    console.print(f"[green]Copy operation complete. {copied_files_count} files copied.[/green]")
    console.print(f"[yellow]{excluded_duplicates_count} duplicate images were excluded.[/yellow]")

if __name__ == "__main__":
    app()
