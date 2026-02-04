
from ultralytics import YOLO
import cv2

model = YOLO(r"C:\Users\kille\agroguard\ml\models\plantvillage\agroguard_20260131_135555\train\weights\best.pt")

def predict(image_path):
    results = model(image_path, conf=0.5)
    for r in results:
        if r.boxes:
            print("Detected:")
            for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
                class_name = model.names[int(cls)]
                print(f"  {class_name} ({conf:.1%})")
            r.save("result.jpg")
        else:
            print("No detection")

predict("test.jpg")
