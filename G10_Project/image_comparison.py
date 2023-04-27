import os
import cv2
from skimage.metrics import structural_similarity as ssim

images_folder = "/home/poseidon/Databases/Image_Database/"

def compare_image(image_path):
    img1 = cv2.imread(image_path)

    unique = True

    image1 = cv2.imread(image_path)
    filename_ls = list(filter(lambda filename : filename.endswith('.jpeg') or filename.endswith('.jpg') or filename.endswith('.png'), os.listdir(images_folder)))

    for filename in filename_ls:
        image2 = cv2.imread(images_folder + filename)

        # Get the dimensions of the first image
        height1, width1, channels1 = image1.shape

        # Get the dimensions of the second image
        height2, width2, channels2 = image2.shape

        # Resize the larger image to the dimensions of the smaller image
        if height1 != height2 or width1 != width2:
            if height1 > height2:
                image1 = cv2.resize(image1, (width2, height2))
            else:
                image2 = cv2.resize(image2, (width1, height1))

        # Convert the images to grayscale
        gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

        # Compute the SSIM score between the two images
        (score, diff) = ssim(gray_image1, gray_image2, full=True)
        score = round(score * 100, 2) # Convert the score to a percentage

        if score >= 65 :
            return {
                "unique": False,
                "filename": filename,
                "similarity": score
            }

    return {
        "unique": True
    }
