import os
import io
import base64
import gradio as gr
from datetime import datetime
import re

from src.predict import predict
from src.medication import get_medication
from src.doctors import find_doctors
from fpdf import FPDF

os.makedirs("/tmp", exist_ok=True)

PRO_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Fraunces:wght@600;700&display=swap');

:root {
    --bg:      #f2f5f9;
    --surface: #ffffff;
    --sur2:    #eaeff5;
    --border:  #d8e2ee;
    --text:    #0d1b2a;
    --text2:   #1e3a52;
    --muted:   #3d5a72;
    --navy:    #0a2540;
    --teal:    #00b4a6;
    --ts:      rgba(0,180,166,0.10);
    --tm:      rgba(0,180,166,0.22);
    --rad:     14px;
    --rsm:     10px;
    --shd:     0 1px 6px rgba(10,37,64,0.08);
}

body.dark-mode {
    --bg:      #0d1b2a;
    --surface: #132233;
    --sur2:    #1a2e42;
    --border:  #233a52;
    --text:    #e8f0f8;
    --text2:   #a8c0d6;
    --muted:   #6a90b0;
    --navy:    #e8f0f8;
    --shd:     0 1px 6px rgba(0,0,0,0.3);
}

*, *::before, *::after { box-sizing: border-box; }

/* Stop blinking/focus borders */
*:focus, *:focus-visible, *:focus-within,
.gradio-container *:focus,
.gradio-container *:focus-visible {
    outline: none !important;
    border-color: var(--border) !important;
    box-shadow: none !important;
}

/* Stop loading animation on output boxes */
.gradio-container .pending,
.gradio-container .generating,
.block.generating,
.block.pending {
    animation: none !important;
    border: 1px solid var(--border) !important;
    transition: none !important;
}

html, body,
.gradio-container,
.gradio-container > *,
.main, .wrap, .gap, .block, .form, .prose,
div[class*="svelte"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', system-ui, sans-serif !important;
    font-size: 15px !important;
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
    border-radius: var(--rad) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shd) !important;
    overflow: hidden !important;
    padding: 0 !important;
}

.gradio-container .gr-group > .gap,
.gradio-container .gr-group > div > .gap {
    padding: 18px 22px !important;
    background: var(--surface) !important;
}

.gradio-container { max-width: 100% !important; padding: 0 28px !important; }

.gradio-container .gr-row,
.gradio-container [class*="row"] {
    display: flex !important;
    flex-direction: row !important;
    gap: 20px !important;
    align-items: stretch !important;
    flex-wrap: nowrap !important;
}

.tabs-nav {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 11px !important;
    padding: 4px !important;
    box-shadow: var(--shd) !important;
    gap: 2px !important;
    width: fit-content !important;
    margin-bottom: 20px !important;
}

.tabs-nav button {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    border-radius: 8px !important;
    padding: 9px 22px !important;
    border: none !important;
    background: transparent !important;
    transition: all 0.2s !important;
}

.tabs-nav button:hover { color: var(--text2) !important; background: var(--sur2) !important; }

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

.gradio-container .gr-image,
.gradio-container [data-testid="image"] {
    background: var(--sur2) !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--rsm) !important;
}

.gradio-container .gr-image > .label-wrap,
.gradio-container [data-testid="image"] .label-wrap {
    display: none !important;
}

.gradio-container input[type="text"],
.gradio-container textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--rsm) !important;
    color: var(--text) !important;
    font-size: 15px !important;
    padding: 11px 14px !important;
}

.btn-main {
    background: linear-gradient(135deg, #0a2540 0%, #0d3060 100%) !important;
    border: none !important;
    border-radius: var(--rsm) !important;
    color: #ffffff !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 14px rgba(10,37,64,0.22) !important;
    transition: all 0.2s !important;
    padding: 14px 20px !important;
    width: 100% !important;
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
    background: var(--sur2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--rsm) !important;
    color: var(--text2) !important;
    font-size: 14px !important;
}

.diq-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 20px 0 16px; border-bottom: 1px solid var(--border); margin-bottom: 22px;
}

.diq-brand { display: flex; align-items: center; gap: 16px; }

.diq-logo {
    width: 62px; height: 62px; border-radius: 17px;
    background: linear-gradient(145deg, #0a2540, #0d3060);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 16px rgba(10,37,64,0.28), inset 0 1px 0 rgba(255,255,255,0.08);
    flex-shrink: 0; position: relative; overflow: hidden;
}

.diq-logo::after {
    content: ''; position: absolute; inset: 0;
    background: linear-gradient(135deg, transparent 50%, rgba(0,180,166,0.22) 100%);
}

.diq-name {
    font-family: 'Fraunces', serif !important;
    font-size: 32px !important; font-weight: 700 !important;
    color: var(--navy) !important; letter-spacing: -0.5px !important; line-height: 1 !important;
}

.diq-name span { color: var(--teal) !important; }

.diq-sub {
    font-size: 12px !important; color: var(--muted) !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
    font-weight: 500 !important; margin-top: 5px !important;
}

.theme-btn {
    display: flex; align-items: center; gap: 8px;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    padding: 8px 18px !important;
    font-size: 14px !important; font-weight: 500 !important;
    color: var(--text2) !important; cursor: pointer !important;
    font-family: 'DM Sans', sans-serif !important;
    box-shadow: var(--shd) !important; transition: all 0.2s !important;
}

.theme-btn:hover { background: var(--sur2) !important; border-color: var(--teal) !important; }

.card-hd {
    display: flex; align-items: center; gap: 12px;
    padding: 15px 22px; border-bottom: 1px solid var(--border);
    background: var(--surface);
}

.card-hd-icon {
    width: 36px; height: 36px; border-radius: 9px;
    background: var(--ts); border: 1px solid var(--tm);
    display: flex; align-items: center; justify-content: center;
    font-size: 17px; flex-shrink: 0;
}

.card-hd-title {
    font-size: 16px !important; font-weight: 600 !important;
    color: var(--text) !important;
}

.hist-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 11px 15px; border-radius: 8px; margin-bottom: 9px;
    background: var(--sur2); border: 1px solid var(--border);
    font-size: 14px; font-weight: 500;
}

.diq-footer {
    margin-top: 32px; padding: 18px 24px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--rad); box-shadow: var(--shd);
    display: flex; align-items: flex-start; gap: 14px;
}

.footer-ico {
    width: 38px; height: 38px; border-radius: 9px;
    background: var(--ts); border: 1px solid var(--tm);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
}

.gradio-container .gr-file {
    background: var(--sur2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--rsm) !important;
}
"""

SEV = {
    "clear":    {"bg":"rgba(0,150,110,0.08)",  "border":"rgba(0,150,110,0.25)",  "color":"#007a56", "label":"Clear Skin",    "sub":"No active acne detected"},
    "mild":     {"bg":"rgba(160,78,0,0.08)",   "border":"rgba(160,78,0,0.25)",   "color":"#9a4a00", "label":"Mild Acne",     "sub":"Minor blemishes — monitor closely"},
    "moderate": {"bg":"rgba(175,70,0,0.08)",   "border":"rgba(175,70,0,0.25)",   "color":"#af4400", "label":"Moderate Acne", "sub":"Consider dermatologist consultation"},
    "severe":   {"bg":"rgba(170,20,20,0.08)",  "border":"rgba(170,20,20,0.25)",  "color":"#a81515", "label":"Severe Acne",   "sub":"Dermatologist consultation recommended"},
}

def ch(icon, title):
    return (
        '<div class="card-hd">'
        '<div class="card-hd-icon">' + icon + '</div>'
        '<div class="card-hd-title">' + title + '</div>'
        '</div>'
    )

def empty(msg):
    return "<div style='text-align:center;padding:40px 0;color:#3d5a72;font-size:15px;'>" + msg + "</div>"

def get_doctors_ui(q=""):
    docs = find_doctors(q)
    if not q.strip():
        return empty("Search by city or pincode to find specialists")
    if not docs:
        return empty("No specialists found for this location.")
    html = '<div style="display:flex;flex-direction:column;gap:12px;">'
    for d in docs:
        html += (
            '<div style="background:#fff;border:1px solid #d8e2ee;border-radius:12px;'
            'padding:16px 20px;display:flex;justify-content:space-between;align-items:center;">'
            '<div>'
            '<div style="font-weight:700;font-size:16px;color:#0d1b2a;">' + d['name'] + '</div>'
            '<div style="font-size:14px;color:#3d5a72;margin-top:3px;">' + d['clinic'] + ' &middot; ' + d['city'] + '</div>'
            '<div style="color:#007a56;font-weight:600;font-size:14px;margin-top:8px;">&#128222; ' + d['phone'] + '</div>'
            '</div>'
            '<a href="' + d['maps_link'] + '" target="_blank" style="text-decoration:none;">'
            '<div style="background:#eaeff5;border:1px solid #d8e2ee;color:#0d1b2a;'
            'padding:9px 18px;border-radius:8px;font-size:14px;font-weight:600;">&#128205; Maps</div>'
            '</a>'
            '</div>'
        )
    return html + "</div>"

def hist_to_html(hist):
    if not hist:
        return empty("No scans recorded yet.")
    html = ""
    for h in hist:
        c = SEV.get(h['severity'], SEV["moderate"])["color"]
        html += (
            '<div class="hist-row">'
            '<span style="color:#3d5a72;">' + h["time"] + '</span>'
            '<span style="font-weight:700;color:' + c + ';text-transform:uppercase;">' + h["severity"] + '</span>'
            '<span style="color:#3d5a72;">' + h["conf"] + '</span>'
            '</div>'
        )
    return html

def analyze_skin_ui(img, hist):
    if not img:
        return [None]*8 + [hist, hist_to_html(hist)]

    res      = predict(img)
    sev      = res["condition"]
    s        = SEV.get(sev, SEV["moderate"])
    conf_val = res["confidence"]
    if isinstance(conf_val, str):
        conf_val = float(conf_val.replace('%', ''))

    badge = (
        '<div style="display:flex;align-items:center;justify-content:space-between;'
        'padding:15px 18px;border-radius:11px;margin-bottom:20px;'
        'background:' + s['bg'] + ';border:1px solid ' + s['border'] + ';">'
        '<div style="display:flex;align-items:center;gap:13px;">'
        '<div style="width:12px;height:12px;border-radius:50%;background:' + s['color'] + ';flex-shrink:0;"></div>'
        '<div>'
        '<div style="font-family:Fraunces,serif;font-size:20px;font-weight:700;color:' + s['color'] + ';">' + s['label'] + '</div>'
        '<div style="font-size:13px;color:#3d5a72;margin-top:2px;">' + s['sub'] + '</div>'
        '</div>'
        '</div>'
        '<div style="font-size:15px;font-weight:700;padding:6px 16px;border-radius:20px;'
        'background:' + s['bg'] + ';color:' + s['color'] + ';border:1px solid ' + s['border'] + ';">'
        + str(round(conf_val, 1)) + '%</div>'
        '</div>'
    )

    bar_w   = str(round(conf_val, 1))
    conf_bar = (
        '<div style="margin-bottom:24px;">'
        '<div style="display:flex;justify-content:space-between;margin-bottom:9px;">'
        '<span style="font-size:13px;font-weight:600;color:#3d5a72;text-transform:uppercase;letter-spacing:0.08em;">AI Diagnostic Confidence</span>'
        '<span style="font-size:14px;font-weight:700;color:' + s['color'] + ';">' + bar_w + '%</span>'
        '</div>'
        '<div style="background:#eaeff5;height:8px;border-radius:5px;overflow:hidden;">'
        '<div style="width:' + bar_w + '%;height:100%;border-radius:5px;background:linear-gradient(90deg,#00b4a6,#0a2540);"></div>'
        '</div>'
        '</div>'
    )

    cls_colors = {"clear":"#007a56","mild":"#9a4a00","moderate":"#af4400","severe":"#a81515"}
    t3 = '<div><div style="font-size:13px;font-weight:600;color:#3d5a72;text-transform:uppercase;letter-spacing:0.09em;margin-bottom:15px;">Top Classifications</div>'
    for cls, val in res["top3"]:
        v  = float(val) if not isinstance(val, str) else float(val.replace('%', ''))
        c  = cls_colors.get(cls, "#3d5a72")
        vs = str(round(v, 1))
        t3 += (
            '<div style="display:flex;align-items:center;gap:13px;margin-bottom:12px;">'
            '<div style="font-size:15px;color:#1e3a52;font-weight:500;width:86px;">' + cls.capitalize() + '</div>'
            '<div style="flex:1;height:7px;background:#eaeff5;border-radius:4px;overflow:hidden;">'
            '<div style="width:' + vs + '%;height:100%;background:' + c + ';border-radius:4px;"></div>'
            '</div>'
            '<div style="font-size:14px;color:#3d5a72;font-weight:600;width:44px;text-align:right;">' + vs + '%</div>'
            '</div>'
        )
    t3 += "</div>"

    med_data = get_medication(sev) or {}
    m_html   = ""
    for m in med_data.get("medicines", []):
        m_html += (
            '<div style="background:#fff;border:1px solid #d8e2ee;border-radius:11px;'
            'padding:17px 20px;margin-bottom:13px;position:relative;overflow:hidden;">'
            '<div style="position:absolute;left:0;top:0;bottom:0;width:3px;background:#00b4a6;"></div>'
            '<div style="font-weight:700;font-size:16px;color:#0d1b2a;margin-bottom:6px;">' + m['name'] + '</div>'
            '<div style="display:inline-block;font-size:11px;font-weight:700;text-transform:uppercase;'
            'background:rgba(0,180,166,0.09);color:#007a70;border:1px solid rgba(0,180,166,0.22);'
            'padding:3px 10px;border-radius:4px;margin-bottom:11px;">' + m['type'] + '</div>'
            '<div style="font-size:14px;color:#1e3a52;line-height:1.65;margin-bottom:10px;">'
            '<b style="color:#0d1b2a;">Use:</b> ' + m['usage'] + '</div>'
            '<div style="font-size:13px;color:#7a3e00;background:rgba(160,78,0,0.07);'
            'border:1px solid rgba(160,78,0,0.18);padding:8px 12px;border-radius:7px;line-height:1.5;">'
            '&#9888; ' + m.get('warning', 'Consult a dermatologist before use.') + '</div>'
            '</div>'
        )

    p_html = '<div style="display:flex;flex-direction:column;">'
    for p in med_data.get("precautions", []):
        p_html += (
            '<div style="display:flex;align-items:flex-start;gap:12px;padding:11px 0;'
            'border-bottom:1px solid #eaeff5;font-size:15px;color:#1e3a52;line-height:1.55;">'
            '<div style="width:22px;height:22px;border-radius:50%;background:rgba(0,180,166,0.09);'
            'border:1px solid rgba(0,180,166,0.22);display:flex;align-items:center;justify-content:center;'
            'flex-shrink:0;color:#007a70;font-size:12px;font-weight:700;margin-top:1px;">&#10003;</div>'
            + p +
            '</div>'
        )
    p_html += "</div>"

    img_b64 = ""
    try:
        from PIL import Image
        pil = Image.open(img)
        pil.thumbnail((500, 500))
        buf = io.BytesIO()
        pil.save(buf, format="JPEG")
        img_b64 = base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        print("Image encode error:", e)

    data_dict = {
        "severity":   sev,
        "confidence": res["confidence"],
        "top3":       res["top3"],
        "meds_list":  med_data.get("medicines", []),
        "precs_list": med_data.get("precautions", []),
        "date":       datetime.now().strftime("%Y-%m-%d %H:%M"),
        "img_b64":    img_b64,
    }

    entry    = {"time": datetime.now().strftime("%H:%M"), "severity": sev, "conf": res["confidence"]}
    new_hist = ([entry] + (hist or []))[:10]

    return (badge, conf_bar, t3, m_html, p_html, data_dict,
            gr.update(visible=True), gr.update(visible=False),
            new_hist, hist_to_html(new_hist))


# PDF
class PDF(FPDF):
    def header(self):
        self.set_font('Times', 'B', 20)
        self.set_text_color(10, 37, 64)
        self.cell(0, 13, 'DermIQ Clinical Report', align='C', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Times', '', 10)
        self.set_text_color(60, 90, 115)
        self.cell(0, 7, 'AI Skin Intelligence Platform - Screening Report', align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(4)

    def footer(self):
        self.set_y(-22)
        self.set_font('Times', 'I', 8)
        self.set_text_color(60, 90, 115)
        self.multi_cell(0, 5, 'MEDICAL DISCLAIMER: FOR SCREENING ONLY. CONFIRM WITH A CERTIFIED PHYSICIAN.', align='C')
        self.cell(0, 6, 'Page ' + str(self.page_no()) + '/{nb}', align='C')


def clean_text(t):
    if not t:
        return ""
    for c in ['💊','⚠','✓','✔️','🚨','📞','📍','🔬','🏥','📄','🕐','⚕️','⚕','⚡','📑','&#9888;','&#10003;','&#128222;','&#128205;']:
        t = t.replace(c, ' ')
    t = re.sub('<[^<]+?>', '', t).strip()
    t = re.sub(r'\s+([,.!?])', r'\1', t)
    t = re.sub(r'([,.!?])(?=[^\s])', r'\1 ', t)
    return t.encode('ascii', 'ignore').decode('ascii').strip()


def create_report(data):
    if not data:
        return None
    try:
        ts   = datetime.now().strftime('%Y%m%d%H%M%S')
        path = "/tmp/DermIQ_" + ts + ".pdf"
        os.makedirs("/tmp", exist_ok=True)

        sev_rgb  = {"SEVERE":(168,21,21),"MODERATE":(175,68,0),"MILD":(154,74,0),"CLEAR":(0,122,86)}
        severity = data['severity'].upper()
        fill     = sev_rgb.get(severity, (0, 180, 166))

        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_font("Times", "B", 16)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(*fill)
        pdf.cell(0, 13, severity + " ACNE DETECTED", align="C", fill=True, new_x='LMARGIN', new_y='NEXT')
        pdf.ln(10)

        NAVY = (10, 37, 64)
        TEAL = (0, 150, 140)

        def section(title):
            pdf.set_font("Times", "B", 13)
            pdf.set_text_color(*TEAL)
            pdf.cell(0, 9, title, new_x='LMARGIN', new_y='NEXT')
            pdf.set_text_color(*NAVY)
            pdf.set_font("Times", "", 11)

        section("1. Diagnostic Metrics")
        pdf.cell(0, 8, "Classification : " + severity.title(), new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 8, "AI Confidence  : " + str(data['confidence']), new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 8, "Date           : " + data['date'], new_x='LMARGIN', new_y='NEXT')
        pdf.ln(7)

        section("2. Recommended Medications")
        for m in data.get("meds_list", []):
            name  = clean_text(m.get("name", ""))
            usage = clean_text(m.get("usage", ""))
            if usage and not usage.endswith('.'):
                usage += '.'
            pdf.multi_cell(0, 7, "- " + name + ": " + usage)
        pdf.ln(5)

        precs = data.get("precs_list", [])
        if precs:
            section("3. Safety Care Protocols")
            for p in precs:
                pc = clean_text(p)
                if pc and not pc.endswith('.'):
                    pc += '.'
                pdf.multi_cell(0, 7, " * " + pc)
        pdf.ln(8)

        if data.get("img_b64"):
            try:
                raw = base64.b64decode(data["img_b64"])
                tmp = "/tmp/tmp_" + ts + ".jpg"
                with open(tmp, "wb") as f:
                    f.write(raw)
                if pdf.get_y() > 170:
                    pdf.add_page()
                pdf.set_font("Times", "B", 11)
                pdf.set_text_color(*TEAL)
                pdf.cell(0, 9, "Clinical Specimen Reference:", align='C', new_x='LMARGIN', new_y='NEXT')
                pdf.ln(2)
                pdf.image(tmp, x=(pdf.w - 100) / 2, w=100)
                os.remove(tmp)
            except Exception as e:
                print("PDF image error:", e)

        pdf.output(path)
        print("PDF saved:", path)
        return path

    except Exception as e:
        print("PDF error:", e)
        return None


# Static HTML (no f-strings to avoid syntax issues)
LOGO_SVG = (
    '<svg width="36" height="36" viewBox="0 0 36 36" fill="none">'
    '<path d="M7 6h10C22.6 6 28 11.9 28 18s-5.4 12-11 12H7V6z" fill="none" stroke="white" stroke-width="2.6" stroke-linejoin="round"/>'
    '<path d="M7 12h9c3.3 0 6 2.7 6 6s-2.7 6-6 6H7" fill="none" stroke="#00d4c4" stroke-width="2.6" stroke-linejoin="round"/>'
    '<line x1="12" y1="18" x2="21" y2="18" stroke="#00b4a6" stroke-width="2" stroke-linecap="round" opacity="0.6"/>'
    '</svg>'
)

HEADER_HTML = (
    '<div class="diq-header">'
    '<div class="diq-brand">'
    '<div class="diq-logo" style="position:relative;z-index:1;">' + LOGO_SVG + '</div>'
    '<div>'
    '<div class="diq-name">Derm<span>IQ</span></div>'
    '<div class="diq-sub">AI Skin Intelligence Platform</div>'
    '</div>'
    '</div>'
    '<button class="theme-btn" onclick="'
    'document.body.classList.toggle(\'dark-mode\');'
    'var dark=document.body.classList.contains(\'dark-mode\');'
    'this.innerHTML=dark?\'&#9728;&#65039; Light Mode\':\'&#127769; Dark Mode\';'
    'var ft=document.getElementById(\'footer-text\');'
    'if(ft) ft.style.color=dark?\'#e8f0f8\':\'#0d1b2a\';'
    'var fs=document.getElementById(\'footer-strong\');'
    'if(fs) fs.style.color=dark?\'#ffffff\':\'#0a2540\';'
    '">&#127769; Dark Mode</button>'
    '</div>'
)

FOOTER_HTML = (
    '<div class="diq-footer">'
    '<div class="footer-ico">&#9877;&#65039;</div>'
    '<div id="footer-text" style="font-size:14px;color:#0d1b2a;line-height:1.7;font-family:DM Sans,sans-serif;">'
    '<strong id="footer-strong" style="color:#0a2540;font-weight:700;">Medical Disclaimer &#8212;</strong> '
    'DermIQ is an AI-powered screening tool for educational purposes only. '
    'Results should not replace professional medical diagnosis. '
    'Always consult a certified dermatologist before starting any treatment.'
    '</div>'
    '</div>'
)

AWAIT_HTML = (
    '<div style="text-align:center;padding:60px 20px;">'
    '<div style="font-size:52px;margin-bottom:18px;opacity:0.35;">&#128300;</div>'
    '<div style="font-size:18px;font-weight:600;color:#0d1b2a;margin-bottom:8px;">Awaiting Analysis</div>'
    '<div style="font-size:15px;color:#3d5a72;">Upload an image and click Analyze Image</div>'
    '</div>'
)


# App layout
with gr.Blocks(title="DermIQ | AI Skin Intelligence") as demo:
    gr.HTML("<style>" + PRO_CSS + "</style>")

    current_data = gr.State(None)
    pred_history = gr.State([])

    gr.HTML(HEADER_HTML)

    with gr.Tabs(elem_classes="tabs-nav"):

        with gr.Tab("Analysis Hub"):
            with gr.Row(equal_height=True):
                with gr.Column(scale=5, min_width=300):
                    with gr.Group(elem_classes="pro-card"):
                        input_photo = gr.Image(
                            label="", type="filepath",
                            height=400, show_label=False
                        )
                        analyze_btn = gr.Button(
                            "⚡ Analyze Image",
                            elem_classes="btn-main", size="lg"
                        )

                with gr.Column(scale=7, min_width=400):
                    with gr.Group(elem_classes="pro-card"):
                        gr.HTML(ch("&#128202;", "Diagnostic Insights"))
                        await_msg = gr.HTML(AWAIT_HTML)
                        with gr.Column(visible=False) as result_outputs:
                            res_badge = gr.HTML()
                            res_conf  = gr.HTML()
                            res_top3  = gr.HTML()

        with gr.Tab("Treatment Guide"):
            with gr.Row():
                with gr.Column(scale=1):
                    with gr.Group(elem_classes="pro-card"):
                        gr.HTML(ch("&#128138;", "Medication Registry"))
                        med_outlet = gr.HTML(empty("Run an analysis first to see medications."))
                with gr.Column(scale=1):
                    with gr.Group(elem_classes="pro-card"):
                        gr.HTML(ch("&#128737;&#65039;", "Safety Care Protocols"))
                        prec_outlet = gr.HTML(empty("Awaiting analysis results."))

        with gr.Tab("Clinical Consultation"):
            with gr.Group(elem_classes="pro-card"):
                gr.HTML(ch("&#127973;", "Board-Certified Specialists"))
                with gr.Row():
                    doc_query = gr.Textbox(
                        placeholder="Search by city or pincode...",
                        show_label=False, scale=5
                    )
                    doc_btn = gr.Button("Find Specialists", elem_classes="btn-main", scale=1)
                doc_list = gr.HTML(get_doctors_ui())

        with gr.Tab("Patient Records"):
            with gr.Row():
                with gr.Column(scale=6):
                    with gr.Group(elem_classes="pro-card"):
                        gr.HTML(ch("&#128196;", "Analysis Report"))
                        no_data_msg = gr.HTML(empty("Run an analysis first, then generate your PDF report here."))
                        report_btn  = gr.Button(
                            "📑 Generate PDF Report",
                            elem_classes="btn-main", visible=False
                        )
                        report_file = gr.File(label="Download your report", visible=False)
                with gr.Column(scale=4):
                    with gr.Group(elem_classes="pro-card"):
                        gr.HTML(ch("&#128336;", "Scan History"))
                        reset_h     = gr.Button("Clear Log", elem_classes="btn-ghost", size="sm")
                        hist_outlet = gr.HTML(hist_to_html([]))

    gr.HTML(FOOTER_HTML)

    # Events
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

    def gen_report(d):
        path = create_report(d)
        if path:
            return gr.update(value=path, visible=True)
        return gr.update(visible=False)

    report_btn.click(fn=gen_report, inputs=[current_data], outputs=[report_file])

    reset_h.click(fn=lambda: ([], hist_to_html([])), outputs=[pred_history, hist_outlet])

if __name__ == "__main__":
    demo.launch()
