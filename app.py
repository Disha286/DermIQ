import os
import io
import base64
import numpy as np
import gradio as gr
from datetime import datetime
import threading
import time

# Custom logic imports
from src.predict import predict
from src.medication import get_medication, get_precautions
from src.doctors import find_doctors
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import re

# Ensure reports directory exists
os.makedirs("reports", exist_ok=True)

# --- PROFESSIONAL DESIGN SYSTEM ---
# High-end Emerald & Midnight Forest Palette
PRO_CSS = """
:root {
    --primary: #059669;
    --primary-light: #10B981;
    --primary-dark: #064E3B;
    --secondary: #64748B;
}

/* Base resets & Premium Clinical Background */
body, .gradio-container {
    background: radial-gradient(circle at 20% 20%, #f0fdf4 0%, #ffffff 100%) !important;
    background-attachment: fixed !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    overflow-x: hidden !important;
}

/* Subtle accent glow */
.gradio-container::before {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(circle at 80% 80%, rgba(16, 185, 129, 0.05) 0%, transparent 50%);
    z-index: -1;
}

.pro-card {
    background: rgba(255, 255, 255, 0.9) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.5) !important;
    box-shadow: 0 20px 80px rgba(2, 44, 34, 0.04) !important;
    border-radius: 32px !important;
    padding: 32px !important;
    transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.pro-card:hover { 
    transform: translateY(-8px) scale(1.01); 
    box-shadow: 0 30px 100px rgba(5, 150, 105, 0.12) !important; 
    border-color: rgba(16, 185, 129, 0.3) !important;
}
.pro-card h3 { color: #064E3B !important; font-weight: 800 !important; font-size: 24px !important; letter-spacing: -0.5px; }

.btn-emerald {
    background: linear-gradient(135deg, #059669 0%, #064E3B 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    color: white !important;
    font-weight: 700 !important;
    box-shadow: 0 8px 20px rgba(5, 150, 105, 0.25) !important;
    transition: all 0.3s ease !important;
}
.btn-emerald:hover { transform: scale(1.02); box-shadow: 0 12px 30px rgba(5, 150, 105, 0.35); }

.tabs-nav {
    border: none !important;
    background: rgba(0, 0, 0, 0.05) !important;
    padding: 6px !important;
    border-radius: 16px !important;
}
button.selected {
    background: #059669 !important;
    color: white !important;
    border-radius: 12px !important;
}

.severity-badge {
    padding: 12px 32px;
    border-radius: 100px;
    font-weight: 800;
    font-size: 18px;
    color: white;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.item-card {
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
}
"""

SEVERITY_COLORS = {
    "clear": {"bg": "linear-gradient(135deg, #059669, #022C22)", "color": "#059669"},
    "mild": {"bg": "linear-gradient(135deg, #F59E0B, #B45309)", "color": "#F59E0B"},
    "moderate": {"bg": "linear-gradient(135deg, #F97316, #C2410C)", "color": "#F97316"},
    "severe": {"bg": "linear-gradient(135deg, #EF4444, #991B1B)", "color": "#EF4444"}
}

# --- FUNCTIONS ---

def get_doctors_ui(q=""):
    docs = find_doctors(q)
    if not q.strip(): return "<p style='text-align:center; padding: 60px 0; opacity: 0.6;'>🔍 Enter City or Pincode to reveal specialist directory</p>"
    if not docs: return "<p style='text-align:center; padding: 40px 0; opacity: 0.6;'>No board-certified specialists found.</p>"
    
    html = '<div style="display: grid; gap: 16px;">'
    for d in docs:
        html += f"""
        <div class="item-card" style="border: 1px solid rgba(5, 150, 105, 0.2); display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-weight: 800; font-size: 18px;">{d['name']}</div>
                <div style="font-size: 14px; opacity: 0.7; margin-top: 4px;">{d['clinic']} | {d['city']}</div>
                <div style="color: #059669; font-weight: 700; margin-top: 8px;">📞 {d['phone']}</div>
            </div>
            <a href="{d['maps_link']}" target="_blank" style="text-decoration: none;">
                <button style="background: rgba(5, 150, 105, 0.1); color: #059669; border: 1px solid #059669; padding: 8px 16px; border-radius: 10px; font-weight: 700; cursor: pointer;">📍 MAPS</button>
            </a>
        </div>
        """
    return html + "</div>"

def analyze_skin_ui(img, hist):
    if not img: 
        return (
            gr.update(value=None, visible=False), # res_badge
            gr.update(value=None, visible=False), # res_conf
            gr.update(value=None, visible=False), # res_top3
            gr.update(value="<p style='text-align:center; padding:40px 0; opacity:0.5;'>Diagnostic data required.</p>"), # med_outlet
            gr.update(value="<p style='text-align:center; padding:40px 0; opacity:0.5;'>Awaiting analysis results.</p>"), # prec_outlet
            None, # current_data
            gr.update(visible=False), # report_btn
            gr.update(visible=True), # no_data_msg
            hist, # pred_history
            hist_to_html(hist), # hist_outlet
            gr.update(visible=True), # await_msg
            gr.update(visible=False) # result_outputs
        )
    
    res = predict(img)
    colors = SEVERITY_COLORS.get(res["condition"], SEVERITY_COLORS["moderate"])
    
    # Enrichment for Premium Report
    # Fetch top 3 doctors for the finder section
    docs_for_report = find_doctors("")[:3]
    
    # Patient metadata (Simulated as per reference)
    patient_info = {
        "name": "Sample User",
        "age": "21",
        "gender": "Female",
        "image_type": "Facial Acne Analysis"
    }

    badge = f'<div class="severity-badge" style="background: {colors["bg"]}; text-align: center;">{res["condition"].upper()} DETECTED</div>'
    
    # Confidence Bar
    conf_val = res["confidence"]
    if isinstance(conf_val, str):
        conf_val = float(conf_val.replace('%',''))
    
    conf_bar = f"""
    <div style="margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="font-weight: 700;">AI Diagnostic Confidence</span>
            <span style="font-weight: 800; color: {colors['color']};">{conf_val:.1f}%</span>
        </div>
        <div style="background: rgba(0,0,0,0.05); height: 12px; border-radius: 6px; overflow: hidden;">
            <div style="width: {conf_val}%; height: 100%; background: {colors['color']}; transition: width 1s;"></div>
        </div>
    </div>
    """
    
    # Top 3
    t3 = '<div style="margin-top:24px;"><h4 style="font-weight:700;margin-bottom:12px;">Top Classifications</h4>'
    for cls, val in res["top3"]:
        v = val
        if isinstance(v, str):
            v = float(v.replace('%',''))
        c = SEVERITY_COLORS.get(cls, SEVERITY_COLORS["moderate"])['color']
        t3 += f'<div style="margin-bottom:8px;"><div style="display:flex;justify-content:space-between;font-size:13px;"><span>{cls.capitalize()}</span><span>{v:.1f}%</span></div><div style="background:rgba(0,0,0,0.03);height:6px;border-radius:3px;margin-top:4px;"><div style="width:{v}%;height:100%;background:{c};"></div></div></div>'
    t3 += "</div>"
    
    # Meds/Precs
    med_data = get_medication(res["condition"]) or {}
    m_html = ""
    for m in med_data.get("medicines", []):
        m_html += f'<div class="item-card" style="border-left: 4px solid #059669; background: rgba(5,150,105,0.05); margin-bottom:12px;">' \
                  f'<div style="font-weight:800;">💊 {m["name"]}</div>' \
                  f'<div style="font-size:12px; opacity:0.8; margin:4px 0;">{m["type"]}</div>' \
                  f'<div style="font-size:13px;"><b>Use:</b> {m["usage"]}</div></div>'
    
    p_html = '<div style="background:rgba(5,150,105,0.03); padding:16px; border-radius:12px;">'
    for p in med_data.get("precautions", []): p_html += f'<div style="margin-bottom:6px;">✔️ {p}</div>'
    p_html += "</div>"
    
    # Report Data
    img_b64 = ""
    try:
        from PIL import Image
        pil = Image.open(img)
        pil.thumbnail((500, 500))
        buf = io.BytesIO()
        pil.save(buf, format="JPEG")
        img_b64 = base64.b64encode(buf.getvalue()).decode()
    except: pass
    
    data_dict = {
        "severity": res["condition"], 
        "confidence": f"{conf_val:.1f}%", 
        "top3": res["top3"], 
        "meds_list": med_data.get("medicines", []), 
        "precs_list": med_data.get("precautions", []), 
        "date": datetime.now().strftime("%d %B %Y"), 
        "time": datetime.now().strftime("%I:%M %p"),
        "img_b64": img_b64,
        "patient": patient_info,
        "doctors": docs_for_report
    }
    entry = {"time": datetime.now().strftime("%H:%M"), "severity": res["condition"], "conf": f"{conf_val:.1f}%"}
    new_hist = ([entry] + (hist or []))[:10]
    
    # Generate PDF in one-shot
    pdf_path = create_report(data_dict)
    
    return (
        gr.update(value=badge, visible=True), # res_badge
        gr.update(value=conf_bar, visible=True), # res_conf
        gr.update(value=t3, visible=True), # res_top3
        m_html, # med_outlet
        p_html, # prec_outlet
        data_dict, # current_data
        gr.update(visible=False), # report_btn (not needed for one-shot but kept hidden)
        gr.update(visible=False), # no_data_msg
        new_hist, # pred_history
        hist_to_html(new_hist), # hist_outlet
        gr.update(visible=False), # await_msg
        gr.update(visible=True), # result_outputs
        gr.update(value=pdf_path, visible=True if pdf_path else False) # report_file
    )

def hist_to_html(hist):
    if not hist: return "<p style='text-align:center; padding:20px; opacity: 0.5;'>History log is empty.</p>"
    html = ""
    for h in hist:
        c = SEVERITY_COLORS.get(h['severity'], SEVERITY_COLORS["moderate"])['color']
        html += f'<div style="background:rgba(0,0,0,0.04); padding:12px; border-radius:12px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">' \
                f'<span>{h["time"]}</span><span style="font-weight:800; color:{c};">{h["severity"].upper()}</span><span>{h["conf"]}</span></div>'
    return html

class PDF(FPDF):
    pass

BASE_DIR = os.path.abspath(os.path.dirname(__file__) if "__file__" in dir() else os.getcwd())

def create_report(data):
    if not data: return None
    reports_dir = os.path.join(BASE_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    t = "DQ-2026-0312-4582"
    path = os.path.join(reports_dir, f"Analysis_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    
    margin = 15
    pdf.set_left_margin(margin)
    pdf.set_right_margin(margin)
    effective_width = pdf.w - 2 * margin

    # Professional Simple Palette
    NAVY = (30, 64, 175)
    GRAY_BORDER = (229, 231, 235)
    TEXT_DARK = (31, 41, 55)
    TEXT_GRAY = (107, 114, 128)
    
    def clean(text):
        if not text: return ""
        text = str(text)
        replacements = {'\U0001f48a': '*', '\U0001f6a8': '!', '💊': '*', '🚨': '!', '✔️': 'v', '✅': 'v', '❌': 'x'}
        for k,v in replacements.items(): text = text.replace(k,v)
        return text.encode('latin-1', 'ignore').decode('latin-1')

    # --- HEADER ---
    pdf.set_font("Times", "B", 20)
    pdf.set_text_color(*NAVY)
    pdf.cell(50, 15, "DermIQ", new_x=XPos.RIGHT, new_y=YPos.TOP)
    
    pdf.set_font("Times", "", 8)
    pdf.set_text_color(*TEXT_GRAY)
    pdf.set_xy(140, 10)
    pdf.cell(25, 4, "Platform:", ln=0)
    pdf.cell(0, 4, "DermIQ AI System", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(140)
    pdf.cell(25, 4, "Date:", ln=0)
    pdf.cell(0, 4, data['date'], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_x(140)
    pdf.cell(25, 4, "Report ID:", ln=0)
    pdf.cell(0, 4, t, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(2)
    pdf.set_draw_color(*GRAY_BORDER)
    pdf.line(margin, pdf.get_y(), 210-margin, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("Times", "B", 12)
    pdf.set_text_color(*NAVY)
    pdf.cell(effective_width, 8, "Dermatological Screening Summary", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # --- PATIENT INFO GRID ---
    p = data.get("patient", {})
    pdf.set_font("Times", "B", 9)
    pdf.set_text_color(*TEXT_DARK)
    pdf.set_fill_color(249, 250, 251)
    
    pdf.cell(25, 6, " Patient Name:", border="TLB", fill=True)
    pdf.set_font("Times", "", 9)
    pdf.cell(55, 6, p.get("name", "User"), border="TRB")
    pdf.set_font("Times", "B", 9)
    pdf.cell(25, 6, " Gender/Age:", border="TLB", fill=True)
    pdf.set_font("Times", "", 9)
    pdf.cell(0, 6, f"{p.get('gender', 'F')} / {p.get('age', '21')}", border="TRB", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Times", "B", 9)
    pdf.cell(25, 6, " Analysis Type:", border="TLB", fill=True)
    pdf.set_font("Times", "", 9)
    pdf.cell(55, 6, p.get("image_type", "Acne Scan"), border="TRB")
    pdf.set_font("Times", "B", 9)
    pdf.cell(25, 6, " Scan Time:", border="TLB", fill=True)
    pdf.set_font("Times", "", 9)
    pdf.cell(0, 6, data.get("time", "10:42 AM"), border="TRB", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    # --- IMAGE & CHART SECTION ---
    y_img_start = pdf.get_y()
    image_h = 35 # fallback
    if data.get("img_b64"):
        try:
            img_data = base64.b64decode(data["img_b64"])
            temp_path = os.path.join(reports_dir, f"temp_{t}.jpg")
            with open(temp_path, "wb") as f: f.write(img_data)
            
            from PIL import Image
            with Image.open(temp_path) as im:
                w, h = im.size
                ratio = min(80 / max(w, 1), 55 / max(h, 1))
                final_w = w * ratio
                final_h = h * ratio
                
            pdf.image(temp_path, x=margin, y=y_img_start, w=final_w, h=final_h)
            image_h = final_h
            os.remove(temp_path)
        except: pass
    
    # Probs on right
    pdf.set_xy(margin + 85, y_img_start)
    pdf.set_font("Times", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(90, 6, "AI Classification Analysis", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font("Times", "", 9)
    pdf.set_text_color(*TEXT_DARK)
    all_conds = ["Clear", "Mild Acne", "Moderate Acne", "Severe Acne"]
    probs = {clean(cls.lower()): float(val) for cls, val in data.get("top3", [])}
    
    for cond in all_conds:
        is_winner = data['severity'].lower() in cond.lower()
        pdf.set_x(margin + 85)
        if is_winner:
            pdf.set_font("Times", "B", 9)
            pdf.set_text_color(185, 28, 28) if "severe" in cond.lower() or "moderate" in cond.lower() else pdf.set_text_color(5, 150, 105)
        else:
            pdf.set_font("Times", "", 9)
            pdf.set_text_color(*TEXT_DARK)
            
        p_val = 0
        for k, v in probs.items():
            if k in cond.lower(): p_val = v
            
        pdf.cell(60, 6, f" {cond}", ln=0)
        pdf.cell(25, 6, f"{p_val:.1f}%", align="R", ln=1)
        pdf.set_draw_color(*GRAY_BORDER)
        pdf.line(margin + 85, pdf.get_y(), margin + 180, pdf.get_y())
    
    pdf.ln(1)
    pdf.set_x(margin + 85)
    pdf.set_font("Times", "BI", 9)
    pdf.set_text_color(*NAVY)
    pdf.cell(90, 6, f"Result: {data['severity'].upper()} ACNE", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    y_chart_bottom = pdf.get_y()
    pdf.set_y(max(y_img_start + image_h, y_chart_bottom) + 5)
    
    # --- FINDINGS & TREATMENT (2-Col) ---
    colw = (effective_width / 2) - 3
    y_base = pdf.get_y() + 2
    
    # Left: Interpretation
    pdf.set_xy(margin, y_base)
    pdf.set_font("Times", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(colw, 6, "Clinical Interpretation", border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", "", 9)
    pdf.set_text_color(*TEXT_DARK)
    pdf.ln(1)
    interps = {"clear": "Healthy skin, no active acne lesions.", "mild": "Occasional comedones/redness.", "moderate": "Multiple pustules and inflammation.", "severe": "Severe cystic inflammation detected."}
    pdf.multi_cell(colw, 4, interps.get(data['severity'].lower(), "Analysis complete."))
    
    pdf.ln(2)
    pdf.set_font("Times", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(colw, 6, "Safety Care Protocols", border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", "", 9)
    pdf.set_text_color(*TEXT_DARK)
    pdf.ln(1)
    for p in ["Wash face twice daily", "Avoid picking", "Use non-comedogenic"]:
        pdf.cell(colw, 4, f" - {p}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Right: Treatment & Doctors
    pdf.set_xy(margin + colw + 6, y_base)
    pdf.set_font("Times", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(colw, 6, "Suggested Care Plan", border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", "", 9)
    pdf.set_text_color(*TEXT_DARK)
    pdf.ln(1)
    for m in data.get("meds_list", [])[:2]:
        pdf.set_x(margin + colw + 6)
        pdf.multi_cell(colw, 4, f"* {clean(m['name'])}")
    
    pdf.ln(2)
    pdf.set_x(margin + colw + 6)
    pdf.set_font("Times", "B", 10)
    pdf.set_text_color(*NAVY)
    pdf.cell(colw, 6, "Local Specialists", border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", "", 8)
    pdf.set_text_color(*TEXT_DARK)
    pdf.ln(1)
    for d in data.get("doctors", []):
        pdf.set_x(margin + colw + 6)
        pdf.cell(colw, 4, f"{clean(d.get('name', ''))} ({clean(d.get('city', ''))})", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # --- FOOTER ---
    pdf.set_y(-25)
    pdf.set_draw_color(*GRAY_BORDER)
    pdf.line(margin, pdf.get_y(), 210-margin, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Times", "I", 7)
    pdf.set_text_color(*TEXT_GRAY)
    pdf.multi_cell(effective_width, 3, "DISCLAIMER: AI screening result for educational use. Not a medical diagnosis. Consult a board-certified professional for final assessment.", align="C")
    pdf.ln(1)
    pdf.set_font("Times", "B", 7)
    pdf.cell(effective_width, 3, "(C) 2026 DermIQ Informatics. All Rights Reserved.", align="C")

    pdf.output(path)
    return path


# --- GRADIO APP ---

with gr.Blocks(title="DermIQ | Clinical Intelligence", css=PRO_CSS) as demo:
    
    current_data = gr.State(None)
    pred_history = gr.State([])
    
    # Global Screen Wrapper
    with gr.Column() as main_screen:
        
        # Professional Header
        with gr.Row(elem_classes="header-wrapper", variant="transparent"):
            with gr.Column():
                gr.HTML("""
                <div style="display: flex; align-items: center; gap: 20px; padding: 20px 0;">
                    <div style="background: #059669; width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 20px rgba(5,150,105,0.3);">
                        <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3"><path d="M12 5v14M5 12h14"/></svg>
                    </div>
                    <div>
                        <div class="logo-text" style="font-size: 36px; font-weight: 900; letter-spacing: -1.5px; color: #0F172A;">DermIQ</div>
                    </div>
                </div>
                """)

        # Dashboard Tabs
        with gr.Tabs(elem_classes="tabs-nav") as nav:
            
            with gr.Tab("Analysis Hub"):
                with gr.Row():
                    with gr.Column(scale=4):
                        with gr.Group(elem_classes="pro-card"):
                            gr.HTML("<h3>Clinical Upload</h3>")
                            input_photo = gr.Image(label="", type="filepath", height=420)
                            analyze_btn = gr.Button("⚡ Analyze Specimen", elem_classes="btn-emerald", size="lg")
                    with gr.Column(scale=6):
                        with gr.Group(elem_classes="pro-card"):
                            gr.HTML("<h3>Diagnostic Insights</h3>")
                            await_msg = gr.HTML("<div style='text-align:center; padding:100px 0; opacity:0.6;'><div style='font-size:48px; margin-bottom:16px;'>🔬</div><div style='font-weight:600;'>Awaiting Capture</div><p>Diagnostic metrics will propagate post-scan.</p></div>")
                            
                            with gr.Column(visible=False) as result_outputs:
                                res_badge = gr.HTML()
                                res_conf = gr.HTML()
                                res_top3 = gr.HTML()

            with gr.Tab("Treatment Guide"):
                with gr.Row():
                    with gr.Column():
                        with gr.Group(elem_classes="pro-card"):
                            gr.HTML("<h3>Medication Registry</h3>")
                            med_outlet = gr.HTML("<p style='text-align:center; padding:40px 0; opacity:0.5;'>Diagnostic data required.</p>")
                    with gr.Column():
                        with gr.Group(elem_classes="pro-card"):
                            gr.HTML("<h3>Safety Care Protocols</h3>")
                            prec_outlet = gr.HTML("<p style='text-align:center; padding:40px 0; opacity:0.5;'>Awaiting analysis results.</p>")

            with gr.Tab("Clinical consultation"):
                with gr.Group(elem_classes="pro-card"):
                    gr.HTML("<h3>Board-Certified Specialists</h3>")
                    with gr.Row():
                        doc_query = gr.Textbox(placeholder="🔍 Search City or Pincode...", show_label=False, scale=5)
                        doc_btn = gr.Button("Fetch Specialists", elem_classes="btn-emerald", scale=1)
                    doc_list = gr.HTML(get_doctors_ui())

            with gr.Tab("Patient Records"):
                with gr.Row():
                    with gr.Column(scale=6):
                        with gr.Group(elem_classes="pro-card"):
                            gr.HTML("<h3>Analysis Report</h3>")
                            report_file = gr.File(label="Encrypted Clinical Report", visible=False)
                            report_btn = gr.Button("📑 Generate PDF", elem_classes="btn-emerald", visible=False)
                            no_data_msg = gr.HTML("<div style='background:rgba(0,0,0,0.05); padding:30px; border-radius:16px; text-align:center;'>No active diagnostic session found.</div>")
                    with gr.Column(scale=4):
                        with gr.Group(elem_classes="pro-card"):
                            with gr.Row():
                                gr.HTML("<h3>Log History</h3>")
                                reset_h = gr.Button("Reset Log", variant="secondary", size="sm")
                            hist_outlet = gr.HTML(hist_to_html([]))

        # Modern Shared Footer
        gr.HTML("""
        <div style="margin-top: 60px; padding-top: 40px; border-top: 1px solid rgba(0,0,0,0.1); text-align: center; padding-bottom: 60px;">
            <div style="background: rgba(185, 28, 28, 0.08); color: #991B1B; padding: 16px 40px; border-radius: 16px; border: 1px solid rgba(185,28,28,0.2); display: inline-block; font-weight: 800; font-size: 14px; margin-bottom: 24px;">
                🚨 MEDICAL DISCLAIMER: FOR SCREENING ONLY. ALWAYS CONFIRM RESULTS WITH A CERTIFIED PHYSICIAN.
            </div>
            <p style="opacity: 0.7; font-size: 14px; font-weight: 600;">DermIQ © 2026. All rights reserved.</p>
        </div>
        """)

    # --- LOGIC ---
    
    analyze_btn.click(
        fn=analyze_skin_ui,
        inputs=[input_photo, pred_history],
        outputs=[res_badge, res_conf, res_top3, med_outlet, prec_outlet, current_data, report_btn, no_data_msg, pred_history, hist_outlet, await_msg, result_outputs, report_file]
    )

    doc_btn.click(get_doctors_ui, inputs=[doc_query], outputs=[doc_list])
    # The dedicated report btn is now a backup/manual trigger
    report_btn.click(lambda d: gr.update(value=create_report(d), visible=True) if d else None, inputs=[current_data], outputs=[report_file])
    reset_h.click(lambda: ([], hist_to_html([])), outputs=[pred_history, hist_outlet])

if __name__ == "__main__":
    demo.launch()
