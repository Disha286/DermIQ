import json

def find_doctors(query):
    with open("data/doctors.json", "r") as f:
        doctors = json.load(f)

    query = query.strip().lower()

    results = [
        d for d in doctors
        if query in d["city"].lower() or query in d["pincode"]
    ]

    for d in results:
        d["maps_link"] = f"https://maps.google.com/?q={d['name'].replace(' ', '+')}+{d['city']}"

    return results[:5]