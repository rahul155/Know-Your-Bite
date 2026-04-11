from ultralytics import YOLO
import torch

# ================= LOAD MODEL =================

# Auto-detect device (GPU if available)
DEVICE = 0 if torch.cuda.is_available() else "cpu"

print(f"YOLO running on: {DEVICE}")

# Load model once (important)
model = YOLO("yolov8n.pt")


# ================= DETECTION FUNCTION =================

def detect_food_items(image_path: str):
    try:
        results = model(
            image_path,
            imgsz=320,     # ⚡ faster inference
            conf=0.3,      # filter weak detections
            device=DEVICE
        )

        items = []

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]

                if label not in items:
                    items.append(label)

        print("Detected items:", items)

        return items

    except Exception as e:
        print("YOLO ERROR:", str(e))
        return []