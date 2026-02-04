# PlantVillage for Object Detection - Dataset

## Información del autor

- **Nombre**: Sebastian Palacio Betancur
- **Email**: spalaciob@unal.edu.co
- **Institución**: Universidad Nacional de Colombia
- **Fecha de Creación**: 9/07/2024

## Descripción del Dataset

Este dataset es una adaptación del ampliamente reconocido PlantVillage (https://data.mendeley.com/datasets/tywbtsjrjv/1), optimizado para tareas de detección de objetos. Contiene imágenes de hojas de plantas anotadas con cajas delimitadoras, lo que facilita el entrenamiento y evaluación de modelos de visión por computadora especializados en identificar enfermedades y condiciones de salud en plantas. Esta versión enriquecida y anotada del dataset original de PlantVillage permite a investigadores y desarrolladores mejorar la precisión de sus modelos de detección de objetos, aprovechando una variedad amplia y representativa de clases de frutas y vegetales.

### Estructura del Dataset

El dataset está organizado en dos carpetas principales:

- `images/`: Contiene las imágenes originales de las hojas.
- `labels/`: Contiene los archivos de etiquetas en formato YOLOv9.

Las imágenes y las etiquetas están nombradas con un prefijo de 4 letras que indica la clase de la enfermedad, seguido del número de imagen.

### Clases

El dataset incluye un total de 38 clases distintas, cada una representando diferentes enfermedades y estados de salud en plantas como manzanas, cerezas, maíz, uvas, tomates, entre otras. Aquí están los códigos y nombres de las clases:

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

### Formato de Etiquetas

Las etiquetas están en formato YOLOv9 con la siguiente estructura:

class_id center_x center_y width height

Por ejemplo:

25 0.49609375 0.5546875 0.984375 0.890625

- `class_id`: ID de la clase, basado en la posición de la clase en la lista.
- `center_x` y `center_y`: Coordenadas del centro del bounding box, normalizadas entre 0 y 1.
- `width` y `height`: Ancho y alto del bounding box, normalizados entre 0 y 1.

