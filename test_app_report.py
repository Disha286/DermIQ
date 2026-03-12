
import sys
import os
# Add current directory to path
sys.path.append(os.getcwd())

from app import create_report
from datetime import datetime

data = {
    "severity": "moderate",
    "confidence": "85.20%",
    "top3": [("moderate", 85.2), ("mild", 10.5), ("severe", 4.3)],
    "meds_list": [{"name": "Clindamycin", "usage": "Twice daily"}],
    "precs_list": ["Avoid sunlight", "Use sunscreen"],
    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "img_b64": None
}

try:
    path = create_report(data)
    print(f"PDF Generated successfully: {path}")
    if os.path.exists(path):
        print(f"File size: {os.path.getsize(path)} bytes")
    else:
        print("File does not exist!")
except Exception as e:
    print(f"Error generating PDF: {e}")
    import traceback
    traceback.print_exc()
