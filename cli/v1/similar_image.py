import cv2
from skimage.metrics import structural_similarity as ssim

# Load images
image1 = cv2.imread('/mnt/d/by_month4/2016-01/IMG_4453.JPG', cv2.IMREAD_GRAYSCALE)
image2 = cv2.imread('/mnt/d/by_month4/2016-01/IMG_4452.jpg', cv2.IMREAD_GRAYSCALE)

# Resize images to the same resolution if necessary
image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))

# Compute SSIM
similarity_index, _ = ssim(image1, image2, full=True)
print(f"SSIM: {similarity_index}")

if similarity_index > 0.9:  # Threshold can be adjusted
    print("Images are similar")
else:
    print("Images are not similar")
