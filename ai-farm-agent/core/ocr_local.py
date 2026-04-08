"""
OCR Local — Le texto da tela usando EasyOCR (sem API, sem custo).
"""

_reader = None

def _get_reader():
    global _reader
    if _reader is None:
        try:
            import easyocr
            _reader = easyocr.Reader(["pt", "en"], gpu=False, verbose=False)
        except Exception as e:
            print(f"  OCR: {e}")
            return None
    return _reader

def read_screen_text(region=None):
    """Le texto visivel na tela."""
    reader = _get_reader()
    if not reader:
        return []
    try:
        from PIL import ImageGrab
        import numpy as np
        screenshot = ImageGrab.grab(bbox=region)
        img_array = np.array(screenshot)
        results = reader.readtext(img_array)
        parsed = []
        for (bbox, text, confidence) in results:
            if confidence > 0.5 and len(text.strip()) > 0:
                x_coords = [p[0] for p in bbox]
                y_coords = [p[1] for p in bbox]
                parsed.append({
                    "text": text.strip(),
                    "bbox": [min(x_coords), min(y_coords), max(x_coords), max(y_coords)],
                    "confidence": round(confidence, 3)
                })
        return parsed
    except Exception as e:
        return []

def find_text_on_screen(target, region=None):
    """Encontra texto especifico na tela."""
    texts = read_screen_text(region)
    target_lower = target.lower()
    for item in texts:
        if target_lower in item["text"].lower():
            bbox = item["bbox"]
            cx = (bbox[0] + bbox[2]) // 2
            cy = (bbox[1] + bbox[3]) // 2
            return {"found": True, "text": item["text"], "center": (cx, cy), "bbox": bbox, "confidence": item["confidence"]}
    return {"found": False}