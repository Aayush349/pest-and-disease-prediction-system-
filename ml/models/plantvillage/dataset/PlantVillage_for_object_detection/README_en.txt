# PlantVillage for Object Detection - Dataset

## Author Information

- **Name**: Sebastian Palacio Betancur
- **Email**: spalaciob@unal.edu.co
- **Institution**: Universidad Nacional de Colombia
- **Creation Date**: July 9, 2024

## Dataset Description

This dataset is an adaptation of the widely recognized PlantVillage, optimized for object detection tasks. It contains annotated images of plant leaves with bounding boxes, facilitating the training and evaluation of computer vision models specialized in identifying diseases and health conditions in plants. This enriched and annotated version of the original PlantVillage dataset enables researchers and developers to enhance the accuracy of their object detection models, leveraging a broad and representative variety of fruit and vegetable classes.

### Dataset Structure

The dataset is organized into two main folders:

- images/: Contains the original leaf images.
- labels/: Contains label files in YOLOv9 format.
Both images and labels are prefixed with a 4-letter code indicating the disease class, followed by the image number.

### Classes

The dataset includes a total of 38 different classes, each representing various diseases and health states in plants such as apples, cherries, corn, grapes, tomatoes, among others. Below are the class codes and names:

| Código | Clase                                       |
|--------|---------------------------------------------|
| APAS   | Apple___Apple_scab                          |
| APBR   | Apple___Black_rot                           |
| APCR   | Apple___Cedar_apple_rust                    |
| APHE   | Apple___healthy                             |
| BLHE   | Blueberry___healthy                         |
| CHPM   | Cherry___Powdery_mildew                     |
| CHHE   | Cherry___healthy                            |
| CCGL   | Corn___Cercospora_leaf_spot Gray_leaf_spot  |
| CCOR   | Corn___Common_rust                          |
| CNLB   | Corn___Northern_Leaf_Blight                 |
| CNHE   | Corn___healthy                              |
| GRBR   | Grape___Black_rot                           |
| GRES   | Grape___Esca_(Black_Measles)                |
| GRLB   | Grape___Leaf_blight_(Isariopsis_Leaf_Spot)  |
| GRHE   | Grape___healthy                             |
| ORHL   | Orange___Haunglongbing_(Citrus_greening)    |
| PCBS   | Peach___Bacterial_spot                      |
| PCHE   | Peach___healthy                             |
| PBBP   | Pepper,_bell___Bacterial_spot               |
| PBHE   | Pepper,_bell___healthy                      |
| PTEB   | Potato___Early_blight                       |
| PTLB   | Potato___Late_blight                        |
| PTHE   | Potato___healthy                            |
| RAHE   | Raspberry___healthy                         |
| SOHE   | Soybean___healthy                           |
| SQPM   | Squash___Powdery_mildew                     |
| STLS   | Strawberry___Leaf_scorch                    |
| STHE   | Strawberry___healthy                        |
| TMBS   | Tomato___Bacterial_spot                     |
| TMEB   | Tomato___Early_blight                       |
| TMLB   | Tomato___Late_blight                        |
| TMLM   | Tomato___Leaf_Mold                          |
| TMSL   | Tomato___Septoria_leaf_spot                 |
| TMSM   | Tomato___Spider_mites Two-spotted_spider_mite |
| TMTS   | Tomato___Target_Spot                        |
| TMYC   | Tomato___Tomato_Yellow_Leaf_Curl_Virus      |
| TMMV   | Tomato___Tomato_mosaic_virus                |
| TMHE   | Tomato___healthy                            |

### Label Format

Labels are in YOLOv9 format with the following structure:

class_id center_x center_y width height

For example:

25 0.49609375 0.5546875 0.984375 0.890625

- class_id: Class ID based on the position of the class in the list.
- center_x and center_y: Coordinates of the bounding box center, normalized between 0 and 1.
- width and height: Width and height of the bounding box, normalized between 0 and 1.