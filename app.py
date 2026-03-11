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
import re

# Ensure reports directory exists
os.makedirs("reports", exist_ok=True)

# --- DESIGN SYSTEM: Modern Minimal Medical ---
PRO_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Fraunces:ital,wght@0,300;0,600;0,700;1,300&display=swap');

:root {
    --navy: #0a2540;
    --navy2: #0d3060;
    --teal: #00b4a6;
    --teal2: #00d4c4;
    --teal-soft: rgba(0,180,166,0.08);
    --teal-mid: rgba(0,180,166,0.18);
    --bg: #f7f9fb;
    --surface: #ffffff;
    --surface2: #f2f5f8;
    --border: #e4eaf0;
    --border2: #cdd8e3;
    --text: #0a2540;
    --text2: #3d5166;
    --muted: #7a92a8;
    --clear-c: #00a67e;
    --mild-c: #d97706;
    --moderate-c: #ea6c0a;
    --severe-c: #dc2626;
    --shadow-sm: 0 1px 4px rgba(10,37,64,0.06);
    --shadow: 0 4px 16px rgba(10,37,64,0.08);
    --shadow-lg: 0 8px 32px rgba(10,37,64,0.11);
    --radius: 14px;
    --radius-sm: 9px;
}

/* ---- BASE ---- */
*, *::before, *::after { box-sizing: border-box; }

body, .gradio-container {
    background: var(--bg) !important;
    font-family: 'DM Sans', -apple-system, sans-serif !important;
    color: var(--text) !important;
}

/* Subtle dot grid background */
.gradio-container::before {
    content: '';
    position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image: radial-gradient(circle, rgba(10,37,64,0.04) 1px, transparent 1px);
    background-size: 22px 22px;
}

/* ---- HEADER ---- */
.dermiq-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 24px 0 20px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
}

.dermiq-brand {
    display: flex;
    align-items: center;
    gap: 14px;
}

.dermiq-logo {
    width: 50px; height: 50px;
    border-radius: 14px;
    background: linear-gradient(145deg, #0a2540 0%, #0d3060 100%);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 14px rgba(10,37,64,0.22), inset 0 1px 0 rgba(255,255,255,0.08);
    flex-shrink: 0;
    position: relative; overflow: hidden;
}

.dermiq-logo::after {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(135deg, transparent 50%, rgba(0,180,166,0.25) 100%);
}

.dermiq-title {
    font-family: 'Fraunces', serif !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    color: var(--navy) !important;
    letter-spacing: -0.5px !important;
    line-height: 1 !important;
    margin: 0 !important;
}

.dermiq-title span { color: var(--teal) !important; }

.dermiq-tagline {
    font-size: 11px !important;
    color: var(--muted) !important;
    letter-spacing: 0.09em !important;
    text-transform: uppercase !important;
    font-weight: 500 !important;
    margin-top: 4px !important;
}

.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: var(--teal);
    background: var(--teal-soft);
    border: 1px solid var(--teal-mid);
    padding: 5px 14px;
    border-radius: 20px;
    font-weight: 600;
    letter-spacing: 0.04em;
}

.live-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--teal);
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.85); }
}

/* ---- TABS ---- */
.tabs-nav {
    border: none !important;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    padding: 4px !important;
    border-radius: 11px !important;
    width: fit-content !important;
    box-shadow: var(--shadow-sm) !important;
    margin-bottom: 24px !important;
}

.tabs-nav button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    border-radius: 8px !important;
    padding: 7px 18px !important;
    border: none !important;
    background: transparent !important;
    transition: all 0.2s !important;
}

.tabs-nav button:hover {
    color: var(--text2) !important;
    background: var(--surface2) !important;
}

.tabs-nav button.selected {
    background: var(--navy) !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(10,37,64,0.18) !important;
}

/* ---- CARDS ---- */
.pro-card {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    box-shadow: var(--shadow-sm) !important;
    padding: 0 !important;
    overflow: hidden !important;
    transition: box-shadow 0.2s !important;
}

.pro-card:hover {
    box-shadow: var(--shadow) !important;
}

.card-head {
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 10px;
    background: var(--surface);
}

.card-head-icon {
    width: 30px; height: 30px;
    border-radius: 7px;
    background: var(--teal-soft);
    border: 1px solid var(--teal-mid);
    display: flex; align-items: center; justify-content: center;
    font-size: 13px;
}

.card-head-title {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    letter-spacing: 0.01em !important;
    margin: 0 !important;
}

/* ---- ANALYZE BUTTON ---- */
.btn-emerald {
    background: linear-gradient(135deg, var(--navy) 0%, #0d3060 100%) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    color: white !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 14px rgba(10,37,64,0.2) !important;
    transition: all 0.2s !important;
    padding: 12px !important;
}

.btn-emerald:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(10,37,64,0.25) !important;
}

/* ---- SEVERITY BADGE ---- */
.severity-badge {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    padding: 13px 16px !important;
    border-radius: var(--radius-sm) !important;
    margin-bottom: 18px !important;
    border: 1px solid !important;
    font-weight: 600 !important;
}

/* ---- ITEM CARD (meds) ---- */
.item-card {
    border-radius: var(--radius-sm) !important;
    padding: 16px !important;
    margin-bottom: 12px !important;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
    position: relative !important;
    overflow: hidden !important;
}

.item-card::before {
    content: '' !important;
    position: absolute !important;
    left: 0; top: 0; bottom: 0 !important;
    width: 3px !important;
    background: var(--teal) !important;
}

/* ---- SEARCH BOX ---- */
.gr-textbox input {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    color: var(--text) !important;
    background: var(--surface) !important;
    padding: 10px 14px !important;
}

.gr-textbox input:focus {
    border-color: var(--teal) !important;
    box-shadow: 0 0 0 3px var(--teal-soft) !important;
    outline: none !important;
}

/* ---- FOOTER ---- */
.dermiq-footer {
    margin-top: 48px;
    padding: 20px 24px;
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 14px;
    background: var(--surface);
    border-radius: var(--radius);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
}

.footer-icon {
    width: 34px; height: 34px;
    border-radius: 8px;
    background: rgba(10,37,64,0.05);
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
}

.footer-text {
    font-size: 12px;
    color: var(--text2);
    line-height: 1.6;
}

.footer-text strong { color: var(--text); }

/* ---- IMAGE UPLOAD ---- */
.gr-image {
    border-radius: var(--radius-sm) !important;
    border: 2px dashed var(--border2) !important;
    background: var(--surface2) !important;
    overflow: hidden !important;
}

.gr-image:hover {
    border-color: var(--teal) !important;
    background: var(--teal-soft) !important;
}

/* History log rows */
.hist-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 14px;
    border-radius: 8px;
    margin-bottom: 8px;
    background: var(--surface2);
    border: 1px solid var(--border);
    font-size: 13px;
}

/* awaiting state */
.await-state {
    text-align: center;
    padding: 60px 0;
    color: var(--muted);
}

.await-icon {
    font-size: 40px;
    margin-bottom: 14px;
    opacity: 0.5;
}

.await-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--text2);
    margin-bottom: 6px;
}

.await-sub {
    font-size: 12px;
    color: var(--muted);
}
"""

SEVERITY_COLORS = {
    "clear":    {"bg": "rgba(0,166,126,0.07)",    "border": "rgba(0,166,126,0.2)",    "color": "#00a67e", "dot": "#00a67e"},
    "mild":     {"bg": "rgba(217,119,6,0.07)",    "border": "rgba(217,119,6,0.2)",    "color": "#d97706", "dot": "#d97706"},
    "moderate": {"bg": "rgba(234,108,10,0.07)",   "border": "rgba(234,108,10,0.2)",   "color": "#ea6c0a", "dot": "#ea6c0a"},
    "severe":   {"bg": "rgba(220,38,38,0.07)",    "border": "rgba(220,38,38,0.2)",    "color": "#dc2626", "dot": "#dc2626"},
}

SEVERITY_LABELS = {
    "clear": "Clear Skin",
    "mild": "Mild Acne",
    "moderate": "Moderate Acne",
    "severe": "Severe Acne",
}

SEVERITY_SUBS = {
    "clear": "No active acne detected",
    "mild": "Minor blemishes — monitor closely",
    "moderate": "Consider dermatologist consultation",
    "severe": "Dermatologist consultation recommended",
}

# --- FUNCTIONS ---

def get_doctors_ui(q=""):
    docs = find_doctors(q)
    if not q.strip():
        return "<div style='text-align:center; padding:50px 0; color:#7a92a8; font-size:13px;'>🔍 Enter a city or pincode to find specialists</div>"
    if not docs:
        return "<div style='text-align:center; padding:40px 0; color:#7a92a8; font-size:13px;'>No specialists found for this location.</div>"

    html = '<div style="display:flex; flex-direction:column; gap:12px;">'
    for d in docs:
        html += f"""
        <div style="background:#fff; border:1px solid #e4eaf0; border-radius:12px; padding:16px 18px;
                    display:flex; justify-content:space-between; align-items:center;
                    box-shadow:0 1px 4px rgba(10,37,64,0.06);">
            <div>
                <div style="font-weight:600; font-size:14px; color:#0a2540;">{d['name']}</div>
                <div style="font-size:12px; color:#7a92a8; margin-top:3px;">{d['clinic']} &middot; {d['city']}</div>
                <div style="color:#00b4a6; font-weight:600; font-size:13px; margin-top:7px;">📞 {d['phone']}</div>
            </div>
            <a href="{d['maps_link']}" target="_blank" style="text-decoration:none;">
                <div style="background:#f2f5f8; border:1px solid #e4eaf0; color:#0a2540;
                            padding:8px 14px; border-radius:8px; font-size:12px; font-weight:600;
                            cursor:pointer; transition:all 0.2s;">📍 Maps</div>
            </a>
        </div>
        """
    return html + "</div>"


def analyze_skin_ui(img, hist):
    if not img:
        return [None]*8 + [hist, hist_to_html(hist)]

    res = predict(img)
    sev = res["condition"]
    colors = SEVERITY_COLORS.get(sev, SEVERITY_COLORS["moderate"])

    conf_val = res["confidence"]
    if isinstance(conf_val, str):
        conf_val = float(conf_val.replace('%', ''))

    # Severity badge
    badge = f"""
    <div style="display:flex; align-items:center; justify-content:space-between;
                padding:13px 16px; border-radius:10px; margin-bottom:18px;
                background:{colors['bg']}; border:1px solid {colors['border']};">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="width:10px; height:10px; border-radius:50%; background:{colors['dot']};
                        box-shadow:0 0 0 3px {colors['border']};"></div>
            <div>
                <div style="font-family:'Fraunces',serif; font-size:17px; font-weight:600; color:{colors['color']};">
                    {SEVERITY_LABELS.get(sev, sev.title())}
                </div>
                <div style="font-size:11px; color:#7a92a8; margin-top:1px;">
                    {SEVERITY_SUBS.get(sev, '')}
                </div>
            </div>
        </div>
        <div style="font-size:13px; font-weight:600; padding:4px 12px; border-radius:20px;
                    background:{colors['bg']}; color:{colors['color']}; border:1px solid {colors['border']};">
            {conf_val:.1f}%
        </div>
    </div>
    """

    # Confidence bar
    conf_bar = f"""
    <div style="margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:7px;">
            <span style="font-size:11px; font-weight:600; color:#7a92a8; text-transform:uppercase; letter-spacing:0.08em;">AI Diagnostic Confidence</span>
            <span style="font-size:12px; font-weight:700; color:{colors['color']};">{conf_val:.1f}%</span>
        </div>
        <div style="background:#f2f5f8; height:6px; border-radius:4px; border:1px solid #e4eaf0; overflow:hidden;">
            <div style="width:{conf_val}%; height:100%; border-radius:4px;
                        background:linear-gradient(90deg, #00b4a6, #0a2540); transition:width 0.8s;"></div>
        </div>
    </div>
    """

    # Top 3 classifications
    t3 = '<div><div style="font-size:11px; font-weight:600; color:#7a92a8; text-transform:uppercase; letter-spacing:0.09em; margin-bottom:12px;">Top Classifications</div>'
    for cls, val in res["top3"]:
        v = float(val) if not isinstance(val, str) else float(val.replace('%', ''))
        c = SEVERITY_COLORS.get(cls, SEVERITY_COLORS["moderate"])["color"]
        t3 += f"""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:9px;">
            <div style="font-size:13px; color:#3d5166; font-weight:500; width:74px;">{cls.capitalize()}</div>
            <div style="flex:1; height:5px; background:#f2f5f8; border-radius:3px; border:1px solid #e4eaf0; overflow:hidden;">
                <div style="width:{v}%; height:100%; background:{c}; border-radius:3px;"></div>
            </div>
            <div style="font-size:12px; color:#7a92a8; font-weight:500; width:38px; text-align:right;">{v:.1f}%</div>
        </div>
        """
    t3 += "</div>"

    # Medications
    med_data = get_medication(sev) or {}
    m_html = ""
    for m in med_data.get("medicines", []):
        m_html += f"""
        <div class="item-card" style="margin-bottom:12px;">
            <div style="font-weight:600; font-size:14px; color:#0a2540; margin-bottom:4px;">{m['name']}</div>
            <div style="display:inline-block; font-size:10px; font-weight:600; letter-spacing:0.08em;
                        text-transform:uppercase; background:rgba(0,180,166,0.08); color:#00b4a6;
                        border:1px solid rgba(0,180,166,0.18); padding:2px 8px; border-radius:4px; margin-bottom:9px;">
                {m['type']}
            </div>
            <div style="font-size:12px; color:#3d5166; line-height:1.6; margin-bottom:8px;">
                <b style="color:#0a2540;">Use:</b> {m['usage']}
            </div>
            <div style="font-size:11px; color:#d97706; background:rgba(217,119,6,0.06);
                        border:1px solid rgba(217,119,6,0.15); padding:6px 10px; border-radius:6px; line-height:1.5;">
                ⚠ {m.get('warning', 'Consult a dermatologist before use.')}
            </div>
        </div>
        """

    # Precautions
    p_html = '<div style="display:flex; flex-direction:column; gap:2px;">'
    for p in med_data.get("precautions", []):
        p_html += f"""
        <div style="display:flex; align-items:flex-start; gap:10px; padding:9px 0;
                    border-bottom:1px solid #f2f5f8; font-size:13px; color:#3d5166; line-height:1.5;">
            <div style="width:18px; height:18px; border-radius:50%; background:rgba(0,180,166,0.08);
                        border:1px solid rgba(0,180,166,0.18); display:flex; align-items:center;
                        justify-content:center; flex-shrink:0; color:#00b4a6; font-size:10px; font-weight:700; margin-top:1px;">✓</div>
            {p}
        </div>
        """
    p_html += "</div>"

    # Image for report
    img_b64 = ""
    try:
        from PIL import Image
        pil = Image.open(img)
        pil.thumbnail((500, 500))
        buf = io.BytesIO()
        pil.save(buf, format="JPEG")
        img_b64 = base64.b64encode(buf.getvalue()).decode()
    except:
        pass

    data_dict = {
        "severity": sev,
        "confidence": res["confidence"],
        "top3": res["top3"],
        "meds_list": med_data.get("medicines", []),
        "precs_list": med_data.get("precautions", []),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "img_b64": img_b64
    }

    entry = {"time": datetime.now().strftime("%H:%M"), "severity": sev, "conf": res["confidence"]}
    new_hist = ([entry] + (hist or []))[:10]

    return badge, conf_bar, t3, m_html, p_html, data_dict, gr.update(visible=True), gr.update(visible=False), new_hist, hist_to_html(new_hist)


def hist_to_html(hist):
    if not hist:
        return "<div style='text-align:center; padding:20px 0; color:#7a92a8; font-size:13px;'>No scans recorded yet.</div>"
    html = ""
    for h in hist:
        c = SEVERITY_COLORS.get(h['severity'], SEVERITY_COLORS["moderate"])['color']
        html += f"""
        <div class="hist-row">
            <span style="color:#7a92a8; font-size:12px;">{h['time']}</span>
            <span style="font-weight:600; color:{c}; font-size:12px; text-transform:uppercase; letter-spacing:0.05em;">{h['severity']}</span>
            <span style="color:#7a92a8; font-size:12px;">{h['conf']}</span>
        </div>
        """
    return html


class PDF(FPDF):
    def header(self):
        self.set_font('Times', 'B', 22)
        self.set_text_color(10, 37, 64)
        self.cell(0, 14, 'DermIQ Clinical Report', align='C', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Times', '', 10)
        self.set_text_color(122, 146, 168)
        self.cell(0, 8, 'AI Skin Intelligence Platform — Screening Report', align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(4)

    def footer(self):
        self.set_y(-25)
        self.set_font('Times', 'I', 8)
        self.set_text_color(122, 146, 168)
        self.multi_cell(0, 5, 'MEDICAL DISCLAIMER: FOR SCREENING ONLY. ALWAYS CONFIRM RESULTS WITH A CERTIFIED PHYSICIAN.', align='C')
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')


def create_report(data):
    if not data: return None
    os.makedirs("reports", exist_ok=True)
    t = datetime.now().strftime('%Y%m%d%H%M%S')
    path = f"reports/DermIQ_Report_{t}.pdf"

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    def clean(text):
        if not text: return ""
        text = text.replace('💊', '-').replace('🚨', '!!!').replace('✔️', '*').replace('⚠', '!')
        text = re.sub('<[^<]+?>', '', text).strip()
        text = re.sub(r'\s+([,.!?])', r'\1', text)
        text = re.sub(r'([,.!?])(?=[^\s])', r'\1 ', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        return text

    severity = data['severity'].upper()
    sev_colors = {
        "SEVERE": (220, 38, 38),
        "MODERATE": (234, 108, 10),
        "MILD": (217, 119, 6),
        "CLEAR": (0, 166, 126)
    }
    fill_color = sev_colors.get(severity, (0, 180, 166))

    pdf.set_font("Times", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(*fill_color)
    pdf.cell(0, 13, f"{severity} ACNE DETECTED", align="C", fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(10)

    NAVY = (10, 37, 64)
    TEAL = (0, 180, 166)

    pdf.set_font("Times", "B", 13)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 10, "1. Diagnostic Metrics", new_x='LMARGIN', new_y='NEXT')
    pdf.set_text_color(*NAVY)
    pdf.set_font("Times", "", 11)
    pdf.cell(0, 8, f"Classification: {severity.title()}", new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 8, f"AI Confidence: {data['confidence']}", new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 8, f"Date: {data['date']}", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(8)

    pdf.set_font("Times", "B", 13)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 10, "2. Recommended Medications", new_x='LMARGIN', new_y='NEXT')
    pdf.set_font("Times", "", 11)
    pdf.set_text_color(*NAVY)
    for m in data.get("meds_list", []):
        name = clean(m.get("name", ""))
        usage = clean(m.get("usage", ""))
        if usage and not usage.endswith('.'): usage += '.'
        pdf.multi_cell(0, 7, f"- {name}: {usage}")
    pdf.ln(6)

    precs = data.get("precs_list", [])
    if precs:
        pdf.set_font("Times", "B", 13)
        pdf.set_text_color(*TEAL)
        pdf.cell(0, 10, "3. Safety Care Protocols", new_x='LMARGIN', new_y='NEXT')
        pdf.set_font("Times", "", 11)
        pdf.set_text_color(*NAVY)
        for p in precs:
            p_clean = clean(p)
            if p_clean and not p_clean.endswith('.'): p_clean += '.'
            pdf.multi_cell(0, 7, f" * {p_clean}")
    pdf.ln(10)

    if data.get("img_b64"):
        try:
            img_data = base64.b64decode(data["img_b64"])
            temp_img = f"reports/temp_{t}.jpg"
            with open(temp_img, "wb") as f:
                f.write(img_data)
            if pdf.get_y() > 170:
                pdf.add_page()
            pdf.set_font("Times", "B", 11)
            pdf.set_text_color(*TEAL)
            pdf.cell(0, 10, "Clinical Specimen Reference:", align='C', new_x='LMARGIN', new_y='NEXT')
            pdf.ln(2)
            img_w = 100
            x_pos = (pdf.w - img_w) / 2
            pdf.image(temp_img, x=x_pos, w=img_w)
            os.remove(temp_img)
        except Exception as e:
            print(f"PDF image error: {e}")

    pdf.output(path)
    return path


# --- GRADIO APP ---

LOGO_SVG = """
<svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M6 5h7.5C17.9 5 22 8.8 22 14s-4.1 9-8.5 9H6V5z"
        fill="none" stroke="white" stroke-width="2.2" stroke-linejoin="round"/>
  <path d="M6 9h6c2.8 0 5 2.2 5 5s-2.2 5-5 5H6"
        fill="none" stroke="#00b4a6" stroke-width="2.2" stroke-linejoin="round"/>
  <line x1="10" y1="14" x2="17" y2="14"
        stroke="#00d4c4" stroke-width="1.5" stroke-linecap="round" opacity="0.7"/>
</svg>
"""

HEADER_HTML = f"""
<div class="dermiq-header">
    <div class="dermiq-brand">
        <div class="dermiq-logo">{LOGO_SVG}</div>
        <div>
            <div class="dermiq-title">Derm<span>IQ</span></div>
            <div class="dermiq-tagline">AI Skin Intelligence Platform</div>
        </div>
    </div>
    <div class="live-badge">
        <div class="live-dot"></div>
        Live · v1.0
    </div>
</div>
"""

FOOTER_HTML = """
<div class="dermiq-footer">
    <div class="footer-icon">⚕️</div>
    <div class="footer-text">
        <strong>Medical Disclaimer —</strong>
        DermIQ is an AI-powered screening tool for educational purposes only.
        Results should not replace professional medical diagnosis.
        Always consult a certified dermatologist before starting any treatment.
    </div>
</div>
"""

AWAIT_HTML = """
<div class="await-state">
    <div class="await-icon">🔬</div>
    <div class="await-title">Awaiting Analysis</div>
    <div class="await-sub">Upload an image and click Analyze Specimen</div>
</div>
"""

with gr.Blocks(title="DermIQ | AI Skin Intelligence", css=PRO_CSS) as demo:

    current_data = gr.State(None)
    pred_history = gr.State([])

    with gr.Column():

        gr.HTML(HEADER_HTML)

        with gr.Tabs(elem_classes="tabs-nav") as nav:

            # ── TAB 1: Analysis Hub ──────────────────────────────────────
            with gr.Tab("Analysis Hub"):
                with gr.Row():
                    with gr.Column(scale=4):
                        with gr.Group(elem_classes="pro-card"):
                            gr.HTML("""
                            <div class="card-head">
                                <div class="card-head-icon">🔬</div>
                                <div class="card-head-title">Clinical Upload</div>
                            </div>
                            """)
                            with gr.Column(elem_id="upload-body", min_width=0):
                                input_photo = gr.Image(label="", type="filepath", height=380)
                                analyze_btn = gr.Button("⚡ Analyze Specimen", elem_classes="btn-emerald", size="lg")

                    with gr.Column(scale=6):
                        with gr.Group(elem_classes="pro-card"):
                            gr.HTML("""
                            <div class="card-head">
                                <div class="card-head-icon">📊</div>
                                <div class="card-head-title">Diagnostic Insights</div>
                            </div>
                            """)
                            with gr.Column(min_width=0):
                                await_msg = gr.HTML(AWAIT_HTML)
                                with gr.Column(visible=False) as result_outputs:
                                    res_badge = gr.HTML()
                                    res_conf = gr.HTML()
                                    res_top3 = gr.HTML()

            # ── TAB 2: Treatment Guide ───────────────────────────────────
            with gr.Tab("Treatment Guide"):
                with gr.Row():
                    with gr.Column():
                        with gr.Group(elem_classes="pro-card"):
                            gr.HTML("""
                            <div class="card-head">
                                <div class="card-head-icon">💊</div>
                                <div class="card-head-title">Medication Registry</div>
                            </div>
                            """)
                            with gr.Column(min_width=0):
                                med_outlet = gr.HTML(
                                    "<div style='text-align:center; padding:40px 0; color:#7a92a8; font-size:13px;'>Run an analysis first to see medications.</div>"
                                )
                    with gr.Column():
                        with gr.Group(elem_classes="pro-card"):
                            gr.HTML("""
                            <div class="card-head">
                                <div class="card-head-icon">🛡️</div>
                                <div class="card-head-title">Safety Care Protocols</div>
                            </div>
                            """)
                            with gr.Column(min_width=0):
                                prec_outlet = gr.HTML(
                                    "<div style='text-align:center; padding:40px 0; color:#7a92a8; font-size:13px;'>Awaiting analysis results.</div>"
                                )

            # ── TAB 3: Clinical Consultation ─────────────────────────────
            with gr.Tab("Clinical Consultation"):
                with gr.Group(elem_classes="pro-card"):
                    gr.HTML("""
                    <div class="card-head">
                        <div class="card-head-icon">🏥</div>
                        <div class="card-head-title">Board-Certified Specialists</div>
                    </div>
                    """)
                    with gr.Column(min_width=0):
                        with gr.Row():
                            doc_query = gr.Textbox(
                                placeholder="Search by city or pincode…",
                                show_label=False, scale=5
                            )
                            doc_btn = gr.Button("Find Specialists", elem_classes="btn-emerald", scale=1)
                        doc_list = gr.HTML(get_doctors_ui())

            # ── TAB 4: Patient Records ───────────────────────────────────
            with gr.Tab("Patient Records"):
                with gr.Row():
                    with gr.Column(scale=6):
                        with gr.Group(elem_classes="pro-card"):
                            gr.HTML("""
                            <div class="card-head">
                                <div class="card-head-icon">📄</div>
                                <div class="card-head-title">Analysis Report</div>
                            </div>
                            """)
                            with gr.Column(min_width=0):
                                no_data_msg = gr.HTML(
                                    "<div style='text-align:center; padding:40px 0; color:#7a92a8; font-size:13px;'>No active diagnostic session.</div>"
                                )
                                report_btn = gr.Button("📑 Generate PDF Report", elem_classes="btn-emerald", visible=False)
                                report_file = gr.File(label="Download Report", visible=False)

                    with gr.Column(scale=4):
                        with gr.Group(elem_classes="pro-card"):
                            gr.HTML("""
                            <div class="card-head">
                                <div class="card-head-icon">🕐</div>
                                <div class="card-head-title">Scan History</div>
                            </div>
                            """)
                            with gr.Column(min_width=0):
                                with gr.Row():
                                    reset_h = gr.Button("Clear Log", variant="secondary", size="sm")
                                hist_outlet = gr.HTML(hist_to_html([]))

        gr.HTML(FOOTER_HTML)

    # --- EVENT LOGIC ---

    analyze_btn.click(
        fn=analyze_skin_ui,
        inputs=[input_photo, pred_history],
        outputs=[res_badge, res_conf, res_top3, med_outlet, prec_outlet,
                 current_data, report_btn, no_data_msg, pred_history, hist_outlet]
    ).then(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True)),
        outputs=[await_msg, result_outputs]
    )

    doc_btn.click(get_doctors_ui, inputs=[doc_query], outputs=[doc_list])
    report_btn.click(
        lambda d: gr.update(value=create_report(d), visible=True),
        inputs=[current_data], outputs=[report_file]
    )
    reset_h.click(lambda: ([], hist_to_html([])), outputs=[pred_history, hist_outlet])


if __name__ == "__main__":
    demo.launch()
