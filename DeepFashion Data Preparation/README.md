
# DeepFashion Data Preparation

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/p?style=flat-square)](https://www.python.org/downloads/)
[![TensorFlow](https://img.shields.io/badge/tensorflow-2-orange)](https://www.tensorflow.org/install)
[![DeepFashion](https://img.shields.io/badge/deepfashion-1-lightgrey)](http://mmlab.ie.cuhk.edu.hk/projects/DeepFashion/InShopRetrieval.html)

[DeepFashion](https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion.html) data contains over 800,000 images collected from various sources. The database is categorized according to four benchmarks; these are Attribute Prediction, Consumer-to-shop Clothes Retrieval, In-shop Clothes Retrieval, and Landmark Detection.

For image semantic segmentation, [In-shop Retrieval](http://mmlab.ie.cuhk.edu.hk/projects/DeepFashion/InShopRetrieval.html) dataset provides images and masks. 

In-shop Clothes Retrieval Benchmark evaluates the performance of in-shop Clothes Retrieval. This is a large subset of DeepFashion, containing large pose and scale variations. It also has large diversities, large quantities, and rich annotations, including

7,982 number of clothing items;

52,712 number of in-shop clothes images, and ~200,000 cross-pose/scale pairs;

Each image is annotated by bounding box, clothing type and pose type.

However, there are issues that need to be taken care of before feeding this dataset to any segmentation algorithm.

The data comes in the form of hierarchy on the left and we need to turn into the format on the right for training:  

![hierarchy](https://user-images.githubusercontent.com/40828825/172366701-29739ca9-95d3-4183-80f9-693ffea8c59b.png)  

Second issue is that all masks have three channels but we may want to make them into one channel as shown below. 

![label_transformation](https://user-images.githubusercontent.com/40828825/172366804-67e8b4c8-b969-4bee-b56e-18ece99a9493.png)  

Lastly, not all images have masks; there are more images than masks. So, we need to take only the images with masks.

The scripts on this folder addresses all these issues. 

## Data import

Zipped data first should be downloaded from <https://drive.google.com/file/d/1TN3FMFT7JA26G0_2syiSBq9ltv6Rb0ui/view?usp=sharing> to the __data__ folder.




## Installation

Install the project

```bash
  git clone \
  --depth 1  \
  --filter=blob:none  \
  --sparse \
https://github.com/hsaltan/Machine-Learning \
;
```

```bash
cd Machine-Learning 
```

```bash
git sparse-checkout set DeepFashion\ Data\ Preparation
```
## Run Locally

```bash
cd Machine-Learning/DeepFashion\ Data\ Preparation
```

First, run ```unzip.py``` to unzip the file.

```bash
python3 unzip.py
```

Then, execute ```make_dataset.py``` to convert the data folder

```bash
python3 make_dataset.py
```

Finally, run ```generate_masks.py``` to convert the masks' three channels to one channel. This conversion will make the mask greyscale by replacing the RGB values with pixel labels. In one channel, each pixel will have only one value representing the class in the image. 16 classes exist in masks, so values are set from 0 to 15. The script, lastly, will zip images and masks.

```bash
python3 generate_masks.py
```



