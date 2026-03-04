import json

def find_doctors(query, max_results: int = 3):
    """Return up to *max_results* doctors matching the city or pincode.

    The returned entries include a Google Maps link for the clinic.
    """
    with open("data/doctors.json", "r") as f:
        doctors = json.load(f)

    query = query.strip().lower()
    if not query:
        return []

    results = [
        d for d in doctors
        if query in d["city"].lower() or query in d["pincode"]
    ]

    for d in results:
        # encode spaces for URLs
        d["maps_link"] = (
            f"https://maps.google.com/?q={d['name'].replace(' ', '+')}+{d['city']}"
        )

    return results[:max_results]