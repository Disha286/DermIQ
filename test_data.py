from src.medication import get_medication, get_precautions
from src.doctors import find_doctors

print("=== Testing Medication ===")
med = get_medication("mild")
print("Status:", med["status"])
print("Medicine:", med["medicines"][0]["name"])
print("Precautions:", get_precautions("mild"))

print("\n=== Testing Doctors ===")
docs = find_doctors("Bangalore")
for d in docs:
    print(d["name"], "-", d["clinic"], "-", d["maps_link"])

print("\nAll good!")