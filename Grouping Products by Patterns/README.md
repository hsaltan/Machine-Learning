# Grouping Products by Patterns

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/p?style=flat-square)](https://www.python.org/downloads/)
[![TensorFlow](https://img.shields.io/badge/tensorflow-2-orange)](https://www.tensorflow.org/install)
[![ESRGAN](https://img.shields.io/badge/ESRGAN-Enhanced_SRGAN-blueviolet)](https://github.com/xinntao/ESRGAN)
[![DeepLab](https://img.shields.io/badge/DeepLab-v3+-blueviolet)](https://arxiv.org/abs/1802.02611)
[![DeepFashion](https://img.shields.io/badge/deepfashion-1-lightgrey)](http://mmlab.ie.cuhk.edu.hk/projects/DeepFashion/InShopRetrieval.html)


In this notebook, I tried to show how we can interpret product patterns and cluster products by those patterns. In doing this, I used clothes as the sample data although any product with a pattern can be the subject of this work.  

There are five stages to accomplish the task:  

1. __Instance segmentation:__ We use DeepLabV3+, a semantic segmentation architecture developed by Google. Semantic segmentation, a computer vision task, assigns semantic labels to every pixel in an image.  

2. __Patch extraction:__ Once every pixel is labeled in the image, we extract a patch from clothing; this will be a segment of the wear to be selected as the target item.  

3. __Image enhancement:__ In case the patch extracted in the previous stage is fairly small in pixel size, we enhance it using the GAN algorithm. The enhancement allows us to use high-resolution images in the upcoming training stages.  

4. __Vectorial representation:__ The patches with or without image enhancement will go through Siamese Network and Triplet Loss architecture that produces their vector representation.  

5. __Clustering:__ As of the last stage, K-Means clustering will group product images by their vectors.  

Not every type of product needs to follow the above five stages. If they have the high-resolution patch image samples, stages 4 to 5 will be enough. In case images need enhancement due to low resolution, stage 3 is the starting point. Products that don't have patch images need to start from the beginning, yet, for this purpose, we need to find a dataset first.

Since we want to label fashion image pixels, we may use a clothing dataset like [DeepFashion](https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion.html).

DeepFashion data contains over 800,000 images collected from various sources. The database is categorized according to four benchmarks; these are Attribute Prediction, Consumer-to-shop Clothes Retrieval, In-shop Clothes Retrieval, and Landmark Detection.  

For the image semantic segmentation, the [In-shop Retrieval](http://mmlab.ie.cuhk.edu.hk/projects/DeepFashion/InShopRetrieval.html) dataset provides both images and masks, and it's the one we are going to use.  

In-shop Clothes Retrieval Benchmark evaluates the performance of in-shop Clothes Retrieval. It is a large subset of DeepFashion, containing large pose and scale variations. It also has large diversities, large quantities, and rich annotations, including  

7,982 number of clothing items;  

52,712 number of in-shop clothes images, and ~200,000 cross-pose/scale pairs;  

Each image is annotated by bounding box, clothing type and pose type.  

However, this dataset has three issues that need to be addressed:  

1. The data comes in the form of a deep file hierarchy and should be reformatted to only image and mask folders under the data directory.  

2. All masks have three channels, but we may want to make them into one channel. Hence, all RGB masks will be greyscale. In the original dataset, pixels are masked with RGB colors. We need to greyscale them by labeling each with a class number. However, RGB colors do not correctly correspond to the names mentioned in the original dataset's `readme.md` file suggests. For example, 255-0-0 does not correspond to headwear but hair. We need to correct such mapping mistakes, and we see that not all RGBs have a label counterpart, and some are N/A. Because not all images have masks, we discard them, and removed clothing types will not have a label. Discarded items are skirts, leggings, bags, neckwears, headwears, eyeglasses, and belts. Actually, some of them do not even exist in the data we used.  
  
As a result, we end up with nine classes, only five of which are clothing types. These are outer, footwear, pants, top and dress. Since our main concern is grouping products by pattern, this is not a worrying point. A pattern on a t-shirt, sweater or jeans doesn't make much difference. We are interested in the patterns of clothes only, not the clothes or their types.  

3. Not all images have masks; there are more images than masks. So, we need to filter in only the images with masks.   
  
Our transformed dataset includes 13,752 pairs of images and masks. The original In-shop Clothes Retrieval Benchmark has 52,712 images and 13,752 masks.  

The script that addresses the above issues can be found [here](https://github.com/hsaltan/Machine-Learning/tree/main/DeepFashion%20Data%20Preparation). In greyscaling masks, we label each pixel with a number from 0 to 15, making 16 distinct classes. The output consists of the renamed and zipped images and masks.  

You can find the original In-shop Clothes Retrieval Benchmark [here](http://mmlab.ie.cuhk.edu.hk/projects/DeepFashion/InShopRetrieval.html). The transformed dataset can be found [here](https://www.kaggle.com/datasets/hserdaraltan/deepfashion-inshop-clothes-retrieval-adjusted).  

This notebook is also in [Kaggle](https://www.kaggle.com/code/hserdaraltan/grouping-products-by-pattern-design).
