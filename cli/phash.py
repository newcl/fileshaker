from PIL import Image
import imagehash
import typer
from pathlib import Path
from itertools import combinations

app = typer.Typer()

def compare_images_in_folder(folder_path: str):
    """
    Calculate perceptual hashes for all images in the folder and compare each pair.
    """
    folder = Path(folder_path)
    # Define all common image file extensions in lowercase for case-insensitive matching
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    
    # Collect all image files in the folder that match the specified extensions (case-insensitive)
    images = [img_path for img_path in folder.iterdir() if img_path.suffix.lower() in image_extensions]

    # Compute pHash for each image and store in a dictionary
    hashes = {}
    for image_path in images:
        image = Image.open(image_path)
        hashes[image_path] = imagehash.phash(image)

    # Compare hashes between every possible pair of images
    for (image1_path, hash1), (image2_path, hash2) in combinations(hashes.items(), 2):

        i1 = int(str(hash1), 16)
        i2 = int(str(hash2), 16)

        print(f"Comparing hash1{hash1}/{i1} and {hash2}/{i2}")

        distance = hash1 - hash2
        print(f"Comparing {image1_path.name} and {image2_path.name}")
        print(f"  Hamming Distance: {distance}")
        similarity_status = "similar" if distance <= 5 else "different"
        print(f"  Result: The images are {similarity_status}.\n")

@app.command()
def main(folder_path: str):
    compare_images_in_folder(folder_path)

if __name__ == "__main__":
    app()
