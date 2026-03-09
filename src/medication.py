import json
import os


def get_medication(class_label: str) -> dict:
    """
    Return medication data for the given severity class label.
    Looks up data/medications.json relative to the project root.
    """
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "medications.json")
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    return data.get(class_label.lower(), {})


def get_precautions(class_label: str) -> list:
    """Return precaution list for the given severity class label."""
    medication = get_medication(class_label)
    return medication.get("precautions", [])