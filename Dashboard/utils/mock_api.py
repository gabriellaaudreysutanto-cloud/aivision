from PIL import Image, ImageDraw
import os
import uuid

def mock_apps():
    return [
        {"id": 1, "name": "Demo App - Rak Minuman"},
        {"id": 2, "name": "Demo App - Snack"},
    ]

def mock_planograms(app_id=None):
    base = [
        {"id": 101, "name": "Planogram Demo A", "app_id": 1},
        {"id": 102, "name": "Planogram Demo B", "app_id": 1},
        {"id": 201, "name": "Planogram Demo Snack", "app_id": 2},
    ]
    if app_id is None:
        return base
    return [p for p in base if p["app_id"] == int(app_id)]

def mock_products():
    return [
        {"id": 1001, "name": "Pocari Sweat 500ml", "brand": "Pocari"},
        {"id": 1002, "name": "Aqua 600ml", "brand": "Aqua"},
        {"id": 1003, "name": "Coca Cola 390ml", "brand": "Coca Cola"},
    ]

def mock_brands():
    return [
        {"id": 11, "name": "Pocari", "category": "Beverage"},
        {"id": 12, "name": "Aqua", "category": "Beverage"},
        {"id": 13, "name": "Coca Cola", "category": "Beverage"},
    ]

from typing import Optional


def mock_analyze_display(image_path: str, request_id: Optional[str] = None):
    if request_id is None:
        request_id = str(uuid.uuid4())

    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size
    draw.rectangle([w*0.1, h*0.1, w*0.55, h*0.65], outline="red", width=6)
    draw.text((w*0.1, h*0.07), "MOCK DETECTION", fill="red")

    os.makedirs("output", exist_ok=True)
    out_path = os.path.join("output", f"{request_id}_output.jpg")
    img.save(out_path, "JPEG", quality=90)

    result = {
        "request_id": request_id,
        "result": {
            "overview": {"status": "ok", "note": "Mock mode (no backend)."},
            "detections": [{"label": "DemoProduct", "confidence": 0.88, "bbox": [0.1, 0.1, 0.55, 0.65]}],
            "product_facing": [{"product": "DemoProduct", "facing": 1}],
            "share_of_space": [{"product": "DemoProduct", "share": 1.0}],
            "planogram": {"compliance": 1.0, "issues": []},
        }
    }
    return result, out_path
