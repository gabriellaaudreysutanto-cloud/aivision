import os
from datetime import datetime
from ultralytics import YOLO
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.getenv("YOLO_MODEL_PATH", os.path.join(BASE_DIR, "models", "best.pt"))
model = None


def get_model():
    global model
    if model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"YOLO model file was not found: {MODEL_PATH}")
        model = YOLO(MODEL_PATH)
    return model


def analyze_display_api(image_path: str, request_id: str, app_id=None, planogram_id=None, run_at=None, pricetag=False):
    try:
        model = get_model()
        results = model.predict(
    source=image_path,
    conf=0.1,
    imgsz=640,
    save=False

        )

        result = results[0]

        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", f"{request_id}_output.jpg")

        plotted = result.plot()
        Image.fromarray(plotted[..., ::-1]).save(output_path)

        detections = []

        if result.boxes is not None:
            for box in result.boxes:
                cls_id = int(box.cls[0].item())
                conf_score = float(box.conf[0].item())
                xyxy = box.xyxy[0].tolist()

                label = model.names.get(cls_id, str(cls_id))

                detections.append({
                    "label": label,
                    "confidence": round(conf_score, 4),
                    "bbox": [round(v, 2) for v in xyxy]
                })

        if run_at is None:
            run_at = datetime.now().isoformat(timespec="seconds")

        return {
            "status": "success",
            "request_id": request_id,
            "app_id": app_id,
            "result": {
                "overview": {
                    "status": "ok",
                    "note": "Inference completed successfully",
                    "run_at": run_at,
                    "output_image_path": output_path,
                    "detection_count": len(detections),
                    "planogram_id": planogram_id,
                    "pricetag": pricetag,
                },
                "detections": detections
            }
        }

    except Exception as e:
        return {
            "status": "failed",
            "request_id": request_id,
            "message": str(e),
            "result": {}
        }


if __name__ == "__main__":
    test_result = analyze_display_api(
        image_path="uploads/WhatsApp Image 2026-04-09 at 12.14.44.jpeg",
        request_id="TEST001"
    )
    print(test_result)
