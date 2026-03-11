from fpdf import FPDF
from datetime import datetime
import os

def generate_pdf(label, confidence, med):
    """Generate a PDF report for the skin condition analysis."""
    pdf = FPDF()
    pdf.add_page()

    # ---- HEADER ----
    pdf.set_fill_color(0, 102, 204)
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 18, "DermIQ", ln=False, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, "AI-Powered Skin Analysis Report", ln=True, align="C")

    # Horizontal rule
    pdf.set_draw_color(0, 102, 204)
    pdf.set_line_width(0.8)
    pdf.line(10, 32, 200, 32)
    pdf.ln(8)

    # ---- DATE ----
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}", ln=True, align="R")
    pdf.ln(4)

    # ---- DIAGNOSIS ----
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, "Diagnosis Result", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"  Condition Detected : {label.capitalize()} Acne", ln=True)
    pdf.cell(0, 8, f"  Confidence Score   : {confidence:.1f}%", ln=True)
    pdf.ln(4)

    # ---- MEDICATION ----
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, "Recommended Medication", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"  Medicine : {med['name']}", ln=True)
    pdf.cell(0, 8, f"  Type     : {med['type']}", ln=True)
    pdf.multi_cell(0, 8, f"  Usage    : {med['usage']}")
    pdf.ln(2)
    pdf.set_text_color(180, 0, 0)
    pdf.set_font("Arial", "B", 10)
    pdf.multi_cell(0, 7, f"  Warning: {med['warning']}")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # ---- PRECAUTIONS ----
    prec = med.get("precautions", [])
    if prec:
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 10, "Precaution Tips", ln=True)
        pdf.set_font("Arial", "", 11)
        for tip in prec:
            pdf.cell(0, 7, f"  * {tip}", ln=True)
        pdf.ln(4)

    # ---- DISCLAIMER ----
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 6,
        "Disclaimer: This report is generated for educational purposes only. "
        "It is not a substitute for professional medical advice. "
        "Always consult a certified dermatologist before starting any treatment."
    )

    # ---- SAVE ----
    os.makedirs("reports", exist_ok=True)
    filename = f"reports/dermiq_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename
