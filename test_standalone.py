"""Standalone test of app functionality without Gradio server."""

from PIL import Image
from src.predict import predict_image
from src.medication import get_medication
from src.doctors import find_doctors
from src.report import generate_pdf
import os
import shutil

def test_analysis(img_path, city_query, class_name):
    """Test a single analysis."""
    print(f"\n[TEST] {class_name.upper()}")
    print("=" * 60)
    
    # Load image
    img = Image.open(img_path)
    print(f"Image loaded: {img_path}")
    
    # Prediction
    result = predict_image(img)
    label = result["class"]
    confidence = result["confidence"]
    top3 = result["top3"]
    print(f"Predicted: {label} ({confidence:.1f}%)")
    print(f"Top 3: {[(c, f'{p:.1f}%') for c, p in top3]}")
    
    # Medication
    med = get_medication(label)
    if isinstance(med.get("medicines"), list) and med["medicines"]:
        med_name = med["medicines"][0].get("name", "N/A")
        med_type = med["medicines"][0].get("type", "N/A")
    else:
        med_name = med.get("name", "N/A")
        med_type = med.get("type", "N/A")
    print(f"Medication: {med_name} ({med_type})")
    
    # Doctors
    doctors = find_doctors(city_query)
    print(f"Doctors found: {len(doctors)}")
    
    # PDF
    # Format medication data as the app expects it
    if isinstance(med.get("medicines"), list) and med["medicines"]:
        med_formatted = {
            "name": med["medicines"][0].get("name", "N/A"),
            "type": med["medicines"][0].get("type", "N/A"),
            "usage": med["medicines"][0].get("usage", "N/A"),
            "warning": med["medicines"][0].get("warning", "Consult a dermatologist"),
            "precautions": med.get("precautions", [])
        }
    else:
        med_formatted = med
    
    pdf_path = generate_pdf(label, confidence, med_formatted)
    print(f"PDF Generated: {pdf_path}")
    
    if os.path.exists(pdf_path):
        pdf_size = os.path.getsize(pdf_path)
        print(f"PDF Size: {pdf_size} bytes")
    else:
        print(f"ERROR: PDF not created")
    
    return pdf_path

if __name__ == "__main__":
    print("[START] DermIQ PDF Generation Test")
    print("=" * 60)
    
    classes = ["clear", "mild", "moderate", "severe"]
    output_dir = "test_results"
    os.makedirs(output_dir, exist_ok=True)
    
    generated_pdfs = []
    
    for class_name in classes:
        test_image_path = f"test_images/{class_name}_test.png"
        try:
            pdf_output_path = test_analysis(test_image_path, "Bangalore", class_name)
            generated_pdfs.append(pdf_output_path)
            
            # Copy to results directory
            output_pdf = os.path.join(output_dir, f"{class_name}_report.pdf")
            shutil.copy(pdf_output_path, output_pdf)
            print(f"Copied to: {output_pdf}")
            
        except RuntimeError as runtime_err:
            print(f"[ERROR] {class_name}: {runtime_err}")
        except IOError as io_err:
            print(f"[ERROR] {class_name}: {io_err}")
    
    print("\n" + "=" * 60)
    print("[SUMMARY]")
    print(f"Tests completed: {len(generated_pdfs)}/{len(classes)}")
    print(f"PDFs saved to: {output_dir}/")
    for pdf_file in generated_pdfs:
        print(f"  - {os.path.basename(pdf_file)}")
