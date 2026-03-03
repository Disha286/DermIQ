import json

def get_medication(class_label):
    with open("data/medications.json", "r") as f:
        data = json.load(f)
    return data.get(class_label.lower(), {})

def get_precautions(class_label):
    medication = get_medication(class_label)
    return medication.get("precautions", [])