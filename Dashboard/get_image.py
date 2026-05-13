import os


def get_image_file(request_id: str, image_type: str = "output", **kwargs):
    # Keep backward compatibility with existing calls like type="output".
    image_type = kwargs.get("type", image_type)
    file_path = os.path.join("output", f"{request_id}_{image_type}.jpg")

    if not os.path.exists(file_path):
        return None

    with open(file_path, "rb") as f:
        return f.read()
