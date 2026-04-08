"""
ScreenCapture v3 — Capturas limpas e minimalistas.
"""

import os, base64
from datetime import datetime
import pyautogui
from PIL import Image, ImageDraw, ImageFont


class ScreenCapture:
    def __init__(self, captures_dir="captures"):
        self.captures_dir = captures_dir
        os.makedirs(captures_dir, exist_ok=True)
        self.records = []

    def capture_step(self, step_number, description, action, result, region=None):
        ts = datetime.now()
        fn = f"step_{step_number:02d}_{ts.strftime('%H%M%S')}.png"
        fp = os.path.join(self.captures_dir, fn)
        try:
            img = pyautogui.screenshot()
            img = self._annotate(img, step_number, action)
            img.save(fp, "PNG", optimize=True)
            rec = {"path":fp,"filename":fn,"step":step_number,"description":description,
                   "action":action,"result":result,"timestamp":ts.isoformat()}
            self.records.append(rec)
            return rec
        except Exception as e:
            rec = {"path":None,"step":step_number,"description":description,
                   "action":action,"result":result,"timestamp":ts.isoformat(),"error":str(e)}
            self.records.append(rec)
            return rec

    def _annotate(self, img, step, action):
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("arial.ttf", 20)
        except:
            try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except: font = ImageFont.load_default()
        txt = f" {step} · {action} "
        bb = draw.textbbox((0,0), txt, font=font)
        w, h = bb[2]-bb[0]+16, bb[3]-bb[1]+12
        draw.rectangle([8,8,8+w,8+h], fill="#000000")
        draw.text((16,12), txt, fill="#00E676", font=font)
        t = datetime.now().strftime("%H:%M:%S")
        draw.text((img.width-100, img.height-28), t, fill="#00BCD4", font=font)
        return img

    def get_records(self): return self.records
    def clear_records(self): self.records = []

    def get_captures_as_base64(self, max_n=5):
        results = []
        for r in self.records[-max_n:]:
            if r.get("path") and os.path.exists(r["path"]):
                with open(r["path"],"rb") as f:
                    results.append({"base64":base64.b64encode(f.read()).decode(),
                        "step":r["step"],"description":r["description"],
                        "action":r["action"],"result":r["result"]})
        return results