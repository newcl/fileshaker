from PIL import Image
import pillow_heif

# Automatically register HEIC support with Pillow
pillow_heif.register_heif_opener()

# Convert HEIC to JPEG
def convert_heic_to_jpeg(input_path, output_path):
    image = Image.open(input_path)
    image = image.convert('RGB')  # Ensure no alpha channel for JPEG
    image.save(output_path, 'JPEG')

# Example usage
convert_heic_to_jpeg('IMG_4233.HEIC', 'output_image.jpeg')
