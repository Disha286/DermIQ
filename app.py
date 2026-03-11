import os
import io
import base64
import gradio as gr
from datetime import datetime
import re

from src.predict import predict
from src.medication import get_medication, get_precautions
from src.doctors import find_doctors
from fpdf import FPDF

os.makedirs("reports", exist_ok=True)

PRO_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Fraunces:wght@600;700&display=swap');

/* ═══════════════════════════════════════════
   CSS VARIABLES — light mode defaults
═══════════════════════════════════════════ */
:root {
    --bg:       #f2f5f9;
    --surface:  #ffffff;
    --surface2: #eaeff5;
    --border:   #d8e2ee;
    --text:     #0a2540;
    --text2:    #2d4a63;
    --muted:    #5a7a96;
    --navy:     #0a2540;
    --teal:     #00b4a6;
    --ts:       rgba(0,180,166,0.10);
    --tm:       rgba(0,180,166,0.22);
    --radius:   14px;
    --rsm:      10px;
    --shadow:   0 1px 6px rgba(10,37,64,0.08);
}

/* Dark mode variables */
body.dark-mode {
    --bg:       #0d1b2a;
    --surface:  #132233;
    --surface2: #1a2e42;
    --border:   #233a52;
    --text:     #e8f0f8;
    --text2:    #a8c0d6;
    --muted:    #6a90b0;
    --navy:     #e8f0f8;
    --shadow:   0 1px 6px rgba(0,0,0,0.3);
}

/* ═══════════════════════════════════════════
   NUCLEAR GRADIO OVERRIDE
═══════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body,
.gradio-container,
.gradio-container > *,
.main, .wrap, .gap, .block, .form, .prose,
div[class*="svelte"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', system-ui, sans-serif !important;
}

.gradio-container .gr-group,
.gradio-container fieldset,
.gradio-container .gr-box,
.gradio-container [class*="block"],
.contain, .gap.compact {
    background: var(--surface) !important;
    border-color: var(--border) !important;
}

.gradio-container .gr-group,
.gradio-container fieldset {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow) !important;
    overflow: hidden !important;
    padding: 0 !important;
}

.gradio-container .gr-group > .gap,
.gradio-container .gr-group > div > .gap {
    padding: 16px 20px !important;
    background: var(--surface) !important;
}

/* Full width container */
.gradio-container {
    max-width: 100% !important;
    padding: 0 32px !important;
}

/* ═══════════════════════════════════════════
   TABS
═══════════════════════════════════════════ */
.tabs-nav {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 11px !important;
    padding: 4px !important;
    box-shadow: var(--shadow) !important;
    gap: 2px !important;
    width: fit-content !important;
}

.tabs-nav button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    border-radius: 8px !important;
    padding: 8px 22px !important;
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
    color: #ffffff !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(10,37,64,0.18) !important;
}

body.dark-mode .tabs-nav button.selected {
    background: var(--teal) !important;
    color: #0a2540 !important;
}

/* ═══════════════════════════════════════════
   INPUTS
═══════════════════════════════════════════ */
.gradio-container .gr-image,
.gradio-container [data-testid="image"] {
    background: var(--surface2) !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--rsm) !important;
}

.gradio-container input[type="text"],
.gradio-container textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--rsm) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
}

.gradio-container input[type="text"]:focus,
.gradio-container textarea:focus {
    border-color: var(--teal) !important;
    box-shadow: 0 0 0 3px var(--ts) !important;
    outline: none !important;
}

/* ═══════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════ */
.btn-main {
    background: linear-gradient(135deg, #0a2540 0%, #0d3060 100%) !important;
    border: none !important;
    border-radius: var(--rsm) !important;
    color: #ffffff !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 14px rgba(10,37,64,0.22) !important;
    transition: all 0.2s ease !important;
    padding: 13px 20px !important;
}

.btn-main:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(10,37,64,0.28) !important;
}

body.dark-mode .btn-main {
    background: linear-gradient(135deg, #00b4a6 0%, #008f84 100%) !important;
    color: #0a2540 !important;
}

.btn-ghost {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--rsm) !important;
    color: var(--text2) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
}

/* ═══════════════════════════════════════════
   HEADER
═══════════════════════════════════════════ */
.diq-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 20px 0 16px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 22px;
}

.diq-brand { display: flex; align-items: center; gap: 16px; }

.diq-logo {
    width: 58px; height: 58px; border-radius: 16px;
    background: linear-gradient(145deg, #0a2540 0%, #0d3060 100%);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 16px rgba(10,37,64,0.25), inset 0 1px 0 rgba(255,255,255,0.08);
    flex-shrink: 0; position: relative; overflow: hidden;
}

.diq-logo::after {
    content: ''; position: absolute; inset: 0;
    background: linear-gradient(135deg, transparent 50%, rgba(0,180,166,0.22) 100%);
}

.diq-name {
    font-family: 'Fraunces', serif !important;
    font-size: 30px !important; font-weight: 700 !important;
    color: var(--navy) !important; letter-spacing: -0.5px !important; line-height: 1 !important;
}

.diq-name span { color: var(--teal) !important; }

.diq-sub {
    font-size: 11px !important; color: var(--muted) !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
    font-weight: 500 !important; margin-top: 5px !important;
}

/* Theme toggle button */
.theme-toggle {
    display: flex; align-items: center; gap: 8px;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    padding: 7px 16px !important;
    font-size: 13px !important; font-weight: 500 !important;
    color: var(--text2) !important;
    cursor: pointer !important; transition: all 0.2s !important;
    font-family: 'DM Sans', sans-serif !important;
    box-shadow: var(--shadow) !important;
}

.theme-toggle:hover {
    background: var(--surface2) !important;
    border-color: var(--teal) !important;
}

/* ═══════════════════════════════════════════
   CARD HEADERS
═══════════════════════════════════════════ */
.card-hd {
    display: flex; align-items: center; gap: 11px;
    padding: 14px 20px; border-bottom: 1px solid var(--border);
    background: var(--surface);
}

.card-hd-icon {
    width: 34px; height: 34px; border-radius: 9px;
    background: var(--ts); border: 1px solid var(--tm);
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
}

.card-hd-title {
    font-size: 15px !important; font-weight: 600 !important;
    color: var(--text) !important; letter-spacing: 0.01em !important;
}

/* ═══════════════════════════════════════════
   AWAIT STATE
═══════════════════════════════════════════ */
.await-wrap {
    text-align: center; padding: 50px 20px;
    background: var(--surface);
}

.await-ico { font-size: 48px; margin-bottom: 16px; opacity: 0.4; }
.await-title { font-size: 17px; font-weight: 600; color: var(--text2); margin-bottom: 8px; }
.await-sub { font-size: 14px; color: var(--muted); }

/* ═══════════════════════════════════════════
   HISTORY ROW
═══════════════════════════════════════════ */
.hist-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;
    background: var(--surface2); border: 1px solid var(--border);
    font-size: 13px; font-weight: 500; color: var(--text2);
}

/* ═══════════════════════════════════════════
   FOOTER
═══════════════════════════════════════════ */
.diq-footer {
    margin-top: 32px; padding: 18px 22px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); box-shadow: var(--shadow);
    display: flex; align-items: flex-start; gap: 14px;
}

.footer-ico {
    width: 36px; height: 36px; border-radius: 9px;
    background: var(--ts); border: 1px solid var(--tm);
    display: flex; align-items: center; justify-content: center;
    font-size: 17px; flex-shrink: 0;
}

.footer-txt { font-size: 13px; color: var(--text2); line-height: 1.65; }
.footer-txt strong { color: var(--text); font-weight: 600; }

/* ═══════════════════════════════════════════
   FILE COMPONENT
═══════════════════════════════════════════ */
.gradio-container .gr-file {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--rsm) !important;
}
"""

SEV = {
    "clear":    {"bg":"rgba(0,150,110,0.08)",  "border":"rgba(0,150,110,0.25)",  "color":"#00966e", "label":"Clear Skin",    "sub":"No active acne detected"},
    "mild":     {"bg":"rgba(180,88,0,0.08)",   "border":"rgba(180,88,0,0.25)",   "color":"#b45800", "label":"Mild Acne",     "sub":"Minor blemishes — monitor closely"},
    "moderate": {"bg":"rgba(196,80,0,0.08)",   "border":"rgba(196,80,0,0.25)",   "color":"#c45000", "label":"Moderate Acne", "sub":"Consider dermatologist consultation"},
    "severe":   {"bg":"rgba(185,28,28,0.08)",  "border":"rgba(185,28,28,0.25)",  "color":"#b91c1c", "label":"Severe Acne",   "sub":"Dermatologist consultation recommended"},
}

def ch(icon, title):
    return f'<div class="card-hd"><div class="card-hd-icon">{icon}</div><div class="card-hd-title">{title}</div></div>'

def empty(msg):
    return f"<div style='text-align:center;padding:36px 0;color:var(--muted,#5a7a96);font-size:14px;'>{msg}</div>"

def get_doctors_ui(q=""):
    docs = find_doctors(q)
    if not q.strip(): return empty("🔍 Enter a city or pincode to find specialists")
    if not docs: return empty("No specialists found for this location.")
    html = '<div style="display:flex;flex-direction:column;gap:12px;">'
    for d in docs:
        html += f"""
        <div style="background:var(--surface,#fff);border:1px solid var(--border,#d8e2ee);
                    border-radius:12px;padding:16px 20px;display:flex;
                    justify-content:space-between;align-items:center;
                    box-shadow:0 1px 4px rgba(10,37,64,0.06);">
            <div>
                <div style="font-weight:600;font-size:15px;color:var(--text,#0a2540);">{d['name']}</div>
                <div style="font-size:13px;color:var(--muted,#5a7a96);margin-top:3px;">{d['clinic']} &middot; {d['city']}</div>
                <div style="color:#00b4a6;font-weight:600;font-size:13px;margin-top:8px;">📞 {d['phone']}</div>
            </div>
            <a href="{d['maps_link']}" target="_blank" style="text-decoration:none;">
                <div style="background:var(--surface2,#eaeff5);border:1px solid var(--border,#d8e2ee);
                            color:var(--text,#0a2540);padding:8px 16px;border-radius:8px;
                            font-size:13px;font-weight:600;cursor:pointer;">📍 Maps</div>
            </a>
        </div>"""
    return html + "</div>"

def hist_to_html(hist):
    if not hist: return empty("No scans recorded yet.")
    html = ""
    for h in hist:
        c = SEV.get(h['severity'], SEV["moderate"])["color"]
        html += f'<div class="hist-row"><span>{h["time"]}</span><span style="font-weight:700;color:{c};text-transform:uppercase;letter-spacing:0.05em;">{h["severity"]}</span><span>{h["conf"]}</span></div>'
    return html

def analyze_skin_ui(img, hist):
    if not img: return [None]*8 + [hist, hist_to_html(hist)]
    res = predict(img)
    sev = res["condition"]
    s   = SEV.get(sev, SEV["moderate"])
    conf_val = res["confidence"]
    if isinstance(conf_val, str): conf_val = float(conf_val.replace('%',''))

    badge = f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:14px 18px;border-radius:10px;margin-bottom:18px;
                background:{s['bg']};border:1px solid {s['border']};">
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="width:11px;height:11px;border-radius:50%;background:{s['color']};
                        box-shadow:0 0 0 3px {s['border']};flex-shrink:0;"></div>
            <div>
                <div style="font-family:'Fraunces',serif;font-size:19px;font-weight:700;color:{s['color']};">{s['label']}</div>
                <div style="font-size:12px;color:#5a7a96;margin-top:2px;">{s['sub']}</div>
            </div>
        </div>
        <div style="font-size:14px;font-weight:700;padding:5px 14px;border-radius:20px;
                    background:{s['bg']};color:{s['color']};border:1px solid {s['border']};">{conf_val:.1f}%</div>
    </div>"""

    conf_bar = f"""
    <div style="margin-bottom:22px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
            <span style="font-size:12px;font-weight:600;color:#5a7a96;text-transform:uppercase;letter-spacing:0.08em;">AI Diagnostic Confidence</span>
            <span style="font-size:13px;font-weight:700;color:{s['color']};">{conf_val:.1f}%</span>
        </div>
        <div style="background:#eaeff5;height:7px;border-radius:4px;border:1px solid #d8e2ee;overflow:hidden;">
            <div style="width:{conf_val}%;height:100%;border-radius:4px;background:linear-gradient(90deg,#00b4a6,#0a2540);"></div>
        </div>
    </div>"""

    cls_colors = {"clear":"#00966e","mild":"#b45800","moderate":"#c45000","severe":"#b91c1c"}
    t3 = '<div><div style="font-size:12px;font-weight:600;color:#5a7a96;text-transform:uppercase;letter-spacing:0.09em;margin-bottom:14px;">Top Classifications</div>'
    for cls, val in res["top3"]:
        v = float(val) if not isinstance(val, str) else float(val.replace('%',''))
        c = cls_colors.get(cls,"#5a7a96")
        t3 += f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:11px;"><div style="font-size:14px;color:#2d4a63;font-weight:500;width:82px;">{cls.capitalize()}</div><div style="flex:1;height:6px;background:#eaeff5;border-radius:3px;border:1px solid #d8e2ee;overflow:hidden;"><div style="width:{v}%;height:100%;background:{c};border-radius:3px;"></div></div><div style="font-size:13px;color:#5a7a96;font-weight:600;width:42px;text-align:right;">{v:.1f}%</div></div>'
    t3 += "</div>"

    med_data = get_medication(sev) or {}
    m_html = ""
    for m in med_data.get("medicines", []):
        m_html += f"""
        <div style="background:#fff;border:1px solid #d8e2ee;border-radius:10px;
                    padding:16px 18px;margin-bottom:12px;position:relative;overflow:hidden;
                    box-shadow:0 1px 4px rgba(10,37,64,0.05);">
            <div style="position:absolute;left:0;top:0;bottom:0;width:3px;background:#00b4a6;"></div>
            <div style="font-weight:700;font-size:15px;color:#0a2540;margin-bottom:5px;">{m['name']}</div>
            <div style="display:inline-block;font-size:11px;font-weight:700;letter-spacing:0.08em;
                        text-transform:uppercase;background:rgba(0,180,166,0.09);color:#00b4a6;
                        border:1px solid rgba(0,180,166,0.2);padding:2px 9px;border-radius:4px;margin-bottom:10px;">{m['type']}</div>
            <div style="font-size:13px;color:#2d4a63;line-height:1.65;margin-bottom:9px;"><b style="color:#0a2540;">Use:</b> {m['usage']}</div>
            <div style="font-size:12px;color:#92550a;background:rgba(202,100,0,0.07);
                        border:1px solid rgba(202,100,0,0.18);padding:7px 11px;border-radius:7px;line-height:1.5;">
                ⚠ {m.get('warning','Consult a dermatologist before use.')}
            </div>
        </div>"""

    p_html = '<div style="display:flex;flex-direction:column;gap:2px;">'
    for p in med_data.get("precautions", []):
        p_html += f'<div style="display:flex;align-items:flex-start;gap:11px;padding:10px 0;border-bottom:1px solid #eaeff5;font-size:14px;color:#2d4a63;line-height:1.55;"><div style="width:20px;height:20px;border-radius:50%;background:rgba(0,180,166,0.09);border:1px solid rgba(0,180,166,0.22);display:flex;align-items:center;justify-content:center;flex-shrink:0;color:#00b4a6;font-size:11px;font-weight:700;margin-top:1px;">✓</div>{p}</div>'
    p_html += "</div>"

    img_b64 = ""
    try:
        from PIL import Image
        pil = Image.open(img); pil.thumbnail((500,500))
        buf = io.BytesIO(); pil.save(buf, format="JPEG")
        img_b64 = base64.b64encode(buf.getvalue()).decode()
    except: pass

    data_dict = {
        "severity": sev, "confidence": res["confidence"], "top3": res["top3"],
        "meds_list": med_data.get("medicines",[]), "precs_list": med_data.get("precautions",[]),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"), "img_b64": img_b64
    }
    entry    = {"time": datetime.now().strftime("%H:%M"), "severity": sev, "conf": res["confidence"]}
    new_hist = ([entry] + (hist or []))[:10]

    return badge, conf_bar, t3, m_html, p_html, data_dict, \
           gr.update(visible=True), gr.update(visible=False), \
           new_hist, hist_to_html(new_hist)

# ── PDF ────────────────────────────────────────────────────────────
class PDF(FPDF):
    def header(self):
        self.set_font('Times','B',20); self.set_text_color(10,37,64)
        self.cell(0,13,'DermIQ Clinical Report',align='C',new_x='LMARGIN',new_y='NEXT')
        self.set_font('Times','',10); self.set_text_color(90,122,150)
        self.cell(0,7,'AI Skin Intelligence Platform — Screening Report',align='C',new_x='LMARGIN',new_y='NEXT')
        self.ln(4)
    def footer(self):
        self.set_y(-22); self.set_font('Times','I',8); self.set_text_color(90,122,150)
        self.multi_cell(0,5,'MEDICAL DISCLAIMER: FOR SCREENING ONLY. ALWAYS CONFIRM WITH A CERTIFIED PHYSICIAN.',align='C')
        self.cell(0,6,f'Page {self.page_no()}/{{nb}}',align='C')

def clean_text(t):
    if not t: return ""
    for ch in ['💊','⚠','✓','✔️','🚨','📞','📍','🔬','🏥','📄','🕐','⚕️','⚕']:
        t = t.replace(ch,' ')
    t = re.sub('<[^<]+?>','',t).strip()
    t = re.sub(r'\s+([,.!?])',r'\1',t)
    t = re.sub(r'([,.!?])(?=[^\s])',r'\1 ',t)
    return t.encode('ascii','ignore').decode('ascii').strip()

def create_report(data):
    if not data: return None
    t    = datetime.now().strftime('%Y%m%d%H%M%S')
    path = f"reports/DermIQ_{t}.pdf"
    os.makedirs("reports", exist_ok=True)
    sev_rgb = {"SEVERE":(185,28,28),"MODERATE":(196,80,0),"MILD":(180,88,0),"CLEAR":(0,150,110)}
    severity = data['severity'].upper()
    fill     = sev_rgb.get(severity,(0,180,166))
    pdf = PDF(); pdf.alias_nb_pages(); pdf.add_page()
    pdf.set_font("Times","B",16); pdf.set_text_color(255,255,255); pdf.set_fill_color(*fill)
    pdf.cell(0,13,f"{severity} ACNE DETECTED",align="C",fill=True,new_x='LMARGIN',new_y='NEXT')
    pdf.ln(10)
    NAVY=(10,37,64); TEAL=(0,180,166)
    def section(title):
        pdf.set_font("Times","B",13); pdf.set_text_color(*TEAL)
        pdf.cell(0,9,title,new_x='LMARGIN',new_y='NEXT')
        pdf.set_text_color(*NAVY); pdf.set_font("Times","",11)
    section("1. Diagnostic Metrics")
    pdf.cell(0,8,f"Classification : {severity.title()}",new_x='LMARGIN',new_y='NEXT')
    pdf.cell(0,8,f"AI Confidence  : {data['confidence']}",new_x='LMARGIN',new_y='NEXT')
    pdf.cell(0,8,f"Date           : {data['date']}",new_x='LMARGIN',new_y='NEXT')
    pdf.ln(7)
    section("2. Recommended Medications")
    for m in data.get("meds_list",[]):
        name=clean_text(m.get("name","")); usage=clean_text(m.get("usage",""))
        if usage and not usage.endswith('.'): usage+='.'
        pdf.multi_cell(0,7,f"- {name}: {usage}")
    pdf.ln(5)
    precs=data.get("precs_list",[])
    if precs:
        section("3. Safety Care Protocols")
        for p in precs:
            pc=clean_text(p)
            if pc and not pc.endswith('.'): pc+='.'
            pdf.multi_cell(0,7,f" * {pc}")
    pdf.ln(8)
    if data.get("img_b64"):
        try:
            raw=base64.b64decode(data["img_b64"]); tmp=f"reports/tmp_{t}.jpg"
            with open(tmp,"wb") as f: f.write(raw)
            if pdf.get_y()>170: pdf.add_page()
            pdf.set_font("Times","B",11); pdf.set_text_color(*TEAL)
            pdf.cell(0,9,"Clinical Specimen Reference:",align='C',new_x='LMARGIN',new_y='NEXT')
            pdf.ln(2); pdf.image(tmp,x=(pdf.w-100)/2,w=100); os.remove(tmp)
        except Exception as e: print(f"PDF img error:{e}")
    pdf.output(path)
    return path

# ── Static HTML ────────────────────────────────────────────────────
LOGO_SVG = """<svg width="34" height="34" viewBox="0 0 34 34" fill="none">
  <path d="M7 6h9C21.1 6 26 11.4 26 17s-4.9 11-10 11H7V6z"
        fill="none" stroke="white" stroke-width="2.5" stroke-linejoin="round"/>
  <path d="M7 11h8c3.3 0 6 2.7 6 6s-2.7 6-6 6H7"
        fill="none" stroke="#00d4c4" stroke-width="2.5" stroke-linejoin="round"/>
  <line x1="11" y1="17" x2="20" y2="17"
        stroke="#00b4a6" stroke-width="1.8" stroke-linecap="round" opacity="0.65"/>
</svg>"""

HEADER_HTML = f"""
<div class="diq-header">
    <div class="diq-brand">
        <div class="diq-logo" style="position:relative;z-index:1;">{LOGO_SVG}</div>
        <div>
            <div class="diq-name">Derm<span>IQ</span></div>
            <div class="diq-sub">AI Skin Intelligence Platform</div>
        </div>
    </div>
    <button class="theme-toggle" onclick="
        document.body.classList.toggle('dark-mode');
        this.textContent = document.body.classList.contains('dark-mode') ? '☀️ Light Mode' : '🌙 Dark Mode';
    ">🌙 Dark Mode</button>
</div>"""

FOOTER_HTML = """
<div class="diq-footer">
    <div class="footer-ico">⚕️</div>
    <div class="footer-txt">
        <strong>Medical Disclaimer —</strong>
        DermIQ is an AI-powered screening tool for educational purposes only.
        Results should not replace professional medical diagnosis.
        Always consult a certified dermatologist before starting any treatment.
    </div>
</div>"""

AWAIT_HTML = """
<div class="await-wrap">
    <div class="await-ico">🔬</div>
    <div class="await-title">Awaiting Analysis</div>
    <div class="await-sub">Upload an image and click Analyze Specimen</div>
</div>"""

# ── App ────────────────────────────────────────────────────────────
with gr.Blocks(title="DermIQ | AI Skin Intelligence", css=PRO_CSS) as demo:

    current_data = gr.State(None)
    pred_history = gr.State([])

    gr.HTML(HEADER_HTML)

    with gr.Tabs(elem_classes="tabs-nav"):

        # ── Analysis Hub ─────────────────────────────────────────────
        with gr.Tab("Analysis Hub"):
            with gr.Row(equal_height=True):
                # LEFT — upload (always visible)
                with gr.Column(scale=4):
                    with gr.Group(elem_classes="pro-card"):
                        input_photo = gr.Image(label="", type="filepath", height=390)
                        analyze_btn = gr.Button("⚡ Analyze Specimen",
                                                elem_classes="btn-main", size="lg")

                # RIGHT — results (always visible)
                with gr.Column(scale=6):
                    with gr.Group(elem_classes="pro-card"):
                        gr.HTML(ch("📊","Diagnostic Insights"))
                        await_msg = gr.HTML(AWAIT_HTML)
                        with gr.Column(visible=False) as result_outputs:
                            res_badge = gr.HTML()
                            res_conf  = gr.HTML()
                            res_top3  = gr.HTML()

        # ── Treatment Guide ──────────────────────────────────────────
        with gr.Tab("Treatment Guide"):
            with gr.Row():
                with gr.Column():
                    with gr.Group(elem_classes="pro-card"):
                        gr.HTML(ch("💊","Medication Registry"))
                        med_outlet = gr.HTML(empty("Run an analysis first to see medications."))
                with gr.Column():
                    with gr.Group(elem_classes="pro-card"):
                        gr.HTML(ch("🛡️","Safety Care Protocols"))
                        prec_outlet = gr.HTML(empty("Awaiting analysis results."))

        # ── Clinical Consultation ────────────────────────────────────
        with gr.Tab("Clinical Consultation"):
            with gr.Group(elem_classes="pro-card"):
                gr.HTML(ch("🏥","Board-Certified Specialists"))
                with gr.Row():
                    doc_query = gr.Textbox(placeholder="Search by city or pincode…",
                                           show_label=False, scale=5)
                    doc_btn   = gr.Button("Find Specialists", elem_classes="btn-main", scale=1)
                doc_list = gr.HTML(get_doctors_ui())

        # ── Patient Records ──────────────────────────────────────────
        with gr.Tab("Patient Records"):
            with gr.Row():
                with gr.Column(scale=6):
                    with gr.Group(elem_classes="pro-card"):
                        gr.HTML(ch("📄","Analysis Report"))
                        no_data_msg = gr.HTML(empty("No active diagnostic session."))
                        report_btn  = gr.Button("📑 Generate PDF Report",
                                                elem_classes="btn-main", visible=False)
                        report_file = gr.File(label="Download Report", visible=False)
                with gr.Column(scale=4):
                    with gr.Group(elem_classes="pro-card"):
                        gr.HTML(ch("🕐","Scan History"))
                        reset_h     = gr.Button("Clear Log",
                                                elem_classes="btn-ghost", size="sm")
                        hist_outlet = gr.HTML(hist_to_html([]))

    gr.HTML(FOOTER_HTML)

    # ── Events ──────────────────────────────────────────────────────
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
        fn=lambda d: gr.update(value=create_report(d), visible=True),
        inputs=[current_data], outputs=[report_file]
    )
    reset_h.click(fn=lambda: ([], hist_to_html([])), outputs=[pred_history, hist_outlet])

if __name__ == "__main__":
    demo.launch()
