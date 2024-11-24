from imagededup.methods import PHash
from PIL import Image
import pillow_heif

# Initialize PHash instance
phasher = PHash()

pillow_heif.register_heif_opener()

image = Image.open('./IMG_4233.HEIC')
image.show()

# Encode an image to get the perceptual hash
hash_value = phasher.encode_image(image_file='./IMG_4233.HEIC')

# Print the hash value
print(f"Hash for the image: {hash_value}")
