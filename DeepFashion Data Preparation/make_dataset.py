import os
import glob
import shutil
import time



cwd = os.getcwd()
main_path = os.path.join(cwd, "data/img_highres", "")
img_path = os.path.join(cwd, "data/images", "")
mask_path = os.path.join(cwd, "data/masks_temp", "")
print("\n")


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


# Create two directories for images and masks
create_directory(img_path)
create_directory(mask_path)


# Get names of directories
def get_directories(path):

    dirs = [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]

    return dirs


# Get filenames in a directory
def get_filenames(path):

    # Create an empty list to store the file names
    filelist = []

    for root, dirs, files in os.walk(path):
        for file in files:

            # Append the file name to the list
            filelist.append(os.path.join(root,file))

    return filelist


# Get and store filenames in their respective lists
def create_path():

    global men_path, women_path

    # Get gender directory names
    gender_dirs = get_directories(main_path)

    # Establish paths for gender directories
 
    men_path = os.path.join(main_path, gender_dirs[0], "")
    women_path = os.path.join(main_path, gender_dirs[1], "")

    men_files = get_filenames(men_path)
    women_files = get_filenames(women_path)

    return men_files, women_files


# Extract the path to a file
def get_dir_path(file_path):

    # Get directory path only
    dir_ = file_path.split("/")[:-1]
    dir_path = "/".join(dir_) + "/"

    return dir_path


# Find the directory path to the file
def find_dir_path():

    # Create lists to store paths to files
    men_dir_list = []
    women_dir_list = []

    men_files, women_files = create_path()

    # Find paths for men
    for men_file in men_files:
        men_dir_list.append(get_dir_path(men_file))

    # Find paths for women
    for women_file in women_files:
        women_dir_list.append(get_dir_path(women_file))

    return men_files, women_files, men_dir_list, women_dir_list


# Eliminate .DS_Store files
def eliminate_unnecessary_files(files):

    for file in files:
        if file.endswith('.DS_Store'):
            os.remove(file)


# Delete directory
def delete_dir(dir_):

    count = 0
    isdir = os.path.isdir(dir_)
    for fname in glob.glob(dir_ + "*"):
        if fname.endswith('.png'):
            count += 1
    if count == 0 and isdir:
        shutil.rmtree(dir_)


# Delete empty directories
# https://www.codegrepper.com/code-examples/python/python+remove+empty+folders
def delete_empty_dirs(dir_):
    # Verify that every empty folder removed in local storage.
    for dirpath, dirnames, filenames in os.walk(dir_, topdown=False):
        if not dirnames and not filenames:
            os.rmdir(dirpath)


def delete_files(png_list, jpg_list):

    # Create a reduced form of jpg and png lists to compare them
    reduced_jpg_list = ["_".join(x.split("/")[-1].split("_")[0:2]) for x in jpg_list]
    reduced_png_list = ["_".join(x.split("/")[-1].split("_")[0:2]) for x in png_list]

    # Store indices of the files to be deleted
    indices = []

    for jpg in reduced_jpg_list:

        # Check if the jpg file has a png counterpart
        if jpg not in reduced_png_list:

            # If no corresponding png file exists, then delete the jpg file. 
            index = reduced_jpg_list.index(jpg)
            indices.append(index)

    deleted_files = [jpg_list[ind] for ind in indices]
    for deleted_file in deleted_files:
        os.remove(deleted_file)


def seperate_jpg_png(dir_):

    jpg_list = []
    png_list = []

    for fname in glob.glob(dir_ + "*"):
        if fname.endswith('.png'):
            png_list.append(fname)
        else:
            jpg_list.append(fname)

    return png_list, jpg_list


# Gather .jpg and .png files in sepaerate lists
def delete_redundant_jpgs():

    # Get updated list of directories and files
    _, _, men_dir_list, women_dir_list = find_dir_path()

    # Seperate jpg and png files in each subdirectory for men
    for dir_ in men_dir_list:
        png_list, jpg_list = seperate_jpg_png(dir_)
        delete_files(png_list, jpg_list)

    # Seperate jpg and png files in each subdirectory for women
    for dir_ in women_dir_list:
        png_list, jpg_list = seperate_jpg_png(dir_)
        delete_files(png_list, jpg_list)


# Delete subdirectories where no .png file exists
def delete_dirs_and_files():

    # Get path to files
    men_files, women_files, men_dir_list, women_dir_list = find_dir_path()

    # Delete men's directories without png file
    for dir_ in men_dir_list:
        delete_dir(dir_)

    # Delete women's directories without png file
    for dir_ in women_dir_list:
        delete_dir(dir_)
    
    print("All directories where no single .png file exists have been successfully deleted.")
    print("\n")

    # Delete empty directories
    delete_empty_dirs(men_path)
    delete_empty_dirs(women_path)

    print("All empty directories have been successfully deleted.")
    print("\n")

    # Delete jpg files that have no corresponding png files
    delete_redundant_jpgs()

    print("All jpg files that have no corresponding png files have been successfully deleted.")
    print("\n")

    # Clean files list
    eliminate_unnecessary_files(men_files)
    eliminate_unnecessary_files(women_files)

    time.sleep(5)


def rename(old_name, new_name):

       # Change the name
        os.rename(old_name, new_name)


# Get extension of the file
def get_extension(object):

    # Check if the file extension is .jpg or .png
    if object.endswith('.jpg'):
        ext = ".jpg"
        path = img_path
    elif object.endswith('.png'):
        ext = ".png"
        path = mask_path

    return ext, path


# Make a new file name
def make_new_filename(dir_elems):

    # Get the filename (last element in the directory path) and split it
    file_elems = dir_elems[-1].split("_")

    # Take first two elements to make up a name
    fname = "".join(file_elems[0:2])

    # Get the extension of file
    extension, path = get_extension(file_elems[-1])

    # Merge the name and the extension
    file_name = fname + extension

    return file_name, path


def make_new_name(files):

    """In the whole directory path, the last four elements are relevant for renaming, e.g.
    MEN/Denim/id_00000080/01_1_front.jpg. We will rename all these four elements.
    To rename the directory part (not the file itself), we take the first three of the
    last four elements in the whole directory path as the last element is the filename."""

 
    for file in files:

        # Break down the path into its subdirectories and files
        dir_elems = file.split("/")

        # Establish a new name for the file
        file_name, path = make_new_filename(dir_elems)

        # Establish new names for the directories
        dir_ = "_".join(file.split("/")[-4:-1])
        dir_name = dir_dict[dir_]

        # Establish new names for the subdirectories
        new_name = path + dir_name + "_" + file_name

        # Rename the file
        rename(file, new_name)


# Make a new directory name
def make_new_directory(all_files):

    # Store unique dir names
    dir_set = set()

    for all_file in all_files:

        # Extract the first three subdirectories and make them a string
        dir_name = "_".join(all_file.split("/")[-4:-1])

        # Add to the set
        dir_set.add(dir_name)

    # Make a list
    dir_list = list(dir_set)

    # Store all unique names in a dictionary
    dir_dict = {v2:str(1_000 + v1) for v1, v2 in enumerate(dir_list)}

    return dir_dict


# Change directory names and move the files
def change_dir_name():

    global dir_dict

    # Get path to files
    men_files, women_files, _, _ = find_dir_path()

    # Concatenate all files
    all_files = men_files + women_files

    # Make a new directory name dictionary
    dir_dict = make_new_directory(all_files)

    # Rename 
    make_new_name(men_files)
    make_new_name(women_files)
    time.sleep(10)

    # Delete empty folders
    delete_dirs_and_files()


delete_dirs_and_files()
change_dir_name()

# Clean up
shutil.rmtree(main_path)

