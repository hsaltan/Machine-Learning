import os
import zipfile



cwd = os.getcwd()
main_path = os.path.join(cwd, "data", "")
zip_file = main_path + 'img_highres_seg.zip'

# Create a ZipFile Object and load sample.zip in it
# https://thispointer.com/python-how-to-unzip-a-file-extract-single-multiple-or-all-files-from-a-zip-archive/
with zipfile.ZipFile(zip_file, 'r') as zipObj:
   # Extract all the contents of zip file in current directory
   zipObj.extractall(main_path)

print("Unzipping is complete!")
print("\n")
