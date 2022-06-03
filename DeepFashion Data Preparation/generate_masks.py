import zipfile
import os
import glob
from matplotlib.pyplot import imread
from PIL import Image
import numpy as np
import time



cwd = os.getcwd()
root_path = os.path.join(cwd, "data", "")
img_path = os.path.join(root_path, "images", "")
mask_path = os.path.join(cwd, "data/masks_temp", "")
new_mask_path = os.path.join(root_path, "masks", "")
print("\n")

# Mask files
masks = glob.glob(mask_path + "*")


# Create directories
def create_directory(path):

    # Check if the directory already exists
    isExist = os.path.exists(path)

    # Create a directory if not exists
    if not isExist:
        os.makedirs(path)
        dir_name = "".join(path.split('/')[-2:-1])
        print(f"New directory <{dir_name}> has been created.")
        print("\n")


# Create a new directory for masks
create_directory(new_mask_path)

# Mask channels
dict_rgb_to_labels = {
                    (0, 0, 0): 0,
                    (255, 250, 250): 1,
                    (250, 235, 215): 2,
                    (70, 130, 180): 3,
                    (16, 78, 139): 4,
                    (255, 250, 205): 5,
                    (255, 140, 0): 6,
                    (50, 205, 50): 7,
                    (220, 220, 220): 8,
                    (255, 0, 0): 9,
                    (127, 255, 212): 10,
                    (0,100, 0): 11,
                    (255, 255, 0): 12,
                    (211, 211, 211): 13,
                    (144, 238, 144): 14,
                    (245, 222, 179): 15
}

print("This will take around 19-20 hours on a single machine...All good things take time!")
print("\n")


# Reduce 4-channel mask to a single channel
def reduce_channel(rgb_mask):
    
    # Unpack channel values and return only one
    b, g, r, a = rgb_mask[:, :, 0], rgb_mask[:, :, 1], rgb_mask[:, :, 2], rgb_mask[:, :, 3]
    
    return r
    

def replace_values(height, width, denorm_img):
    
    # Iterate over rows and columns
    for h in range(height):
        for w in range(width):
            
            # Find the r,g,b values in a pixel and make them a tuple
            tuple_key = tuple(denorm_img[h][w][:3])
            # Get the corresponding label for the pixel r-g-b tuple, and
            # replace the array values with the label
            denorm_img[h][w][:3] = dict_rgb_to_labels[tuple_key]
            
    return denorm_img


# Get the height and width of image
def get_height_width(img_np_arr):
    
    # Height of the image
    height = img_np_arr.shape[0]
    
    # Width of the image
    width = img_np_arr.shape[1]
     
    return height, width

    
# Denormalize and change the value type of image
def denormalize_array(img_np_arr):
    
    # Denormalize image
    denorm_img_arr = img_np_arr * 255.0

    # Convert to integer
    int_img_array = denorm_img_arr.astype(np.uint8)
    
    return int_img_array


# Read image as numpy array
def read_image(image):

    mask_image = imread(image)

    return mask_image
    
    
def generate_mask_image(image, i):

    # Read image as numpy array
    img_np_arr = read_image(image)
    
    # Denormalize image and change its values to integer
    denorm_img = denormalize_array(img_np_arr)
    
    # Get height and width of the image
    height, width = get_height_width(denorm_img)
    
    # Create a mask with 4 channels
    rgb_mask = replace_values(height, width, denorm_img)
    
    # Reduce the mask to a single channel
    mask = reduce_channel(rgb_mask)
    
    # Convert from array to image
    mask_png = Image.fromarray(mask)

    # Save image to new folder
    new_name = new_mask_path + image.split("/")[-1]
    mask_png.save(new_name)

    print(f"{i+1}.\t{image}\tis reformatted.")


for i, mask in enumerate(masks):

    # Generate new masks
    generate_mask_image(mask, i)

print("\n")
print("All mask images have been successfully reformatted.")
print("\n")

time.sleep(5)


# Zip image and mask files
# https://www.codegrepper.com/code-examples/python/frameworks/file-path-in-python/python+zip+multiple+folder+subfolders+and+files
def zipfolder(foldername, target_dir):
    zipobj = zipfile.ZipFile(foldername + '.zip', 'w', zipfile.ZIP_DEFLATED)
    rootlen = len(target_dir)
    for base, dirs, files in os.walk(target_dir):
        for file in files:
            fn = os.path.join(base, file)
            if ("images" in fn or "masks" in fn) and "masks_temp" not in fn:
                zipobj.write(fn, fn[rootlen:])


# Zip files
zip_file_name = "deepfashion1_data"
zipfolder(zip_file_name, root_path)

# Rename the zip file
old_name = cwd + "/" + zip_file_name + ".zip"
new_name = root_path + zip_file_name + ".zip"
os.rename(old_name, new_name)

print("Image and mask files have been zipped, and then renamed.")
print("\n")
