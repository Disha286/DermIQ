import json
import os


def find_doctors(query: str, max_results: int = 5):
    """
    Search dermatologists by city name or PIN code.
    Returns up to max_results matching records with a Google Maps link.
    """
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "doctors.json")
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            doctors = json.load(f)
    except Exception:
        return []

    q = (query or "").strip().lower()

    if q:
        results = [
            d for d in doctors
            if q in str(d.get("city", "")).lower() or q in str(d.get("pincode", "")).lower()
        ]
    else:
        results = doctors

    for d in results[:max_results]:
        name = d.get("name", "").replace(" ", "+")
        city = d.get("city", "")
        d["maps_link"] = f"https://maps.google.com/?q={name}+{city}"

    return results[:max_results]
