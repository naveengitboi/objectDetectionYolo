from ultralytics import YOLO

model = YOLO("yolov8n.pt")


# Train the model on the COCO8 example dataset for 100 epochs
results = model.train(data="coco8.yaml", epochs=1)

# Run inference with the YOLOv8n model on the 'bus.jpg' image
results = model("path/to/bus.jpg")