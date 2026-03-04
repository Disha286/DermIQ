import gradio as gr
from src.predict import predict_image
from src.medication import get_medication
from src.doctors import find_doctors
from src.report import generate_pdf

history = []

def clear_history():
    history.clear()
    return "<p style='color:gray'>History cleared.</p>"

def analyze(image, city_query):

    # --- Prediction ---
    result = predict_image(image)
    label = result["class"]
    confidence = result["confidence"]
    top3 = result["top3"]

    # --- Medication & Doctors ---
    med = get_medication(label)
    # Get first medicine from list if available
    if isinstance(med.get("medicines"), list) and med["medicines"]:
        med_data = med["medicines"][0]
        med_formatted = {
            "name": med_data.get("name", "N/A"),
            "type": med_data.get("type", "N/A"),
            "usage": med_data.get("usage", "N/A"),
            "warning": med_data.get("warning", "Consult a dermatologist"),
            "precautions": med.get("precautions", [])
        }
    else:
        # Fallback for flat structure
        med_formatted = {
            "name": med.get("name", "Consult dermatologist"),
            "type": med.get("type", "N/A"),
            "usage": med.get("usage", "N/A"),
            "warning": med.get("warning", "Consult a dermatologist"),
            "precautions": med.get("precautions", [])
        }
    
    doctors = find_doctors(city_query)

    # --- Save to history ---
    from datetime import datetime
    history.insert(0, {
        "label": label,
        "confidence": confidence,
        "time": datetime.now().strftime("%H:%M:%S")
    })
    if len(history) > 5:
        history.pop()

    # --- Generate PDF ---
    pdf_path = generate_pdf(label, confidence, med_formatted)

    # =====================
    # BUILD ALL HTML BLOCKS
    # =====================

    # Severity badge
    severity_map = {
        "clear":    ("[C]", "#2e7d32", "Low Severity"),
        "mild":     ("[M]", "#f9a825", "Mild Severity"),
        "moderate": ("[Mo]", "#e65100", "Moderate Severity"),
        "severe":   ("[S]", "#c62828", "High Severity"),
    }
    icon, color, sev_label = severity_map.get(label, ("⚪", "#555", "Unknown"))
    badge_html = f"""
    <div style="display:inline-block;background:{color};color:white;
    padding:8px 18px;border-radius:20px;font-size:15px;font-weight:700;margin-bottom:12px">
      {icon} {label.capitalize()} — {sev_label}
    </div>
    """

    # Confidence progress bar
    conf_html = f"""
    <div style="margin:10px 0 16px">
      <div style="font-size:13px;margin-bottom:4px">
        <b>Confidence Score:</b> {confidence:.1f}%
      </div>
      <div style="background:#e0e0e0;border-radius:8px;height:16px;overflow:hidden">
        <div style="background:{color};width:{confidence}%;height:16px;
        border-radius:8px;transition:width 0.5s ease"></div>
      </div>
    </div>
    """

    # Top-3 predictions
    top3_rows = "".join([
        f"""<div style="margin:4px 0">
          <span style="width:90px;display:inline-block">{cls.capitalize()}</span>
          <div style="display:inline-block;background:#e3f2fd;border-radius:6px;
          height:12px;width:{prob}%;vertical-align:middle"></div>
          <b style="margin-left:6px">{prob:.1f}%</b>
        </div>""" for cls, prob in top3
    ])
    top3_html = f"""
    <div style="background:#f5f5f5;border-radius:10px;padding:14px;margin-bottom:14px">
      <div style="font-weight:700;margin-bottom:8px">[TOP-3] Predictions</div>
      {top3_rows}
    </div>
    """

    # Medication card
    med_html = f"""
    <div style="background:#e8f5e9;border:1px solid #a5d6a7;border-radius:12px;
    padding:16px;margin-bottom:14px">
      <div style="font-size:15px;font-weight:700;margin-bottom:10px">[RX] Recommended Medication</div>
      <table style="width:100%;font-size:13px;border-collapse:collapse">
        <tr><td style="padding:4px 0;color:#555;width:100px">Medicine</td>
            <td><b>{med_formatted['name']}</b></td></tr>
        <tr><td style="padding:4px 0;color:#555">Type</td>
            <td><span style="background:#c8e6c9;padding:2px 10px;
            border-radius:10px;font-size:11px;font-weight:600">{med_formatted['type']}</span></td></tr>
        <tr><td style="padding:4px 0;color:#555">Usage</td>
            <td>{med_formatted['usage']}</td></tr>
      </table>
      <div style="background:#ffebee;border-left:4px solid #e53935;padding:8px 12px;
      border-radius:4px;margin-top:10px;font-size:12px">
        [!] <b>Warning:</b> {med_formatted['warning']}
      </div>
    </div>
    """

    # Precaution tips
    prec = med_formatted.get("precautions", [])
    prec_items = "".join([f"<li style='margin:4px 0'>{p}</li>" for p in prec])
    prec_html = f"""
    <div style="background:#fff8e1;border:1px solid #ffe082;border-radius:12px;
    padding:14px;margin-bottom:14px">
      <div style="font-weight:700;margin-bottom:8px">[SHIELD] Precaution Tips</div>
      <ul style="margin:0;padding-left:18px;font-size:13px">{prec_items}</ul>
    </div>
    """ if prec else ""

    # Doctor suggestion cards (3 in a row)
    doc_cards = "".join([
        f"""<div style="background:white;border:1px solid #ddd;border-radius:10px;
        padding:12px;flex:1;min-width:180px">
          <div style="font-weight:700;font-size:13px">[MD] {d['name']}</div>
          <div style="font-size:12px;color:#555;margin-top:4px">[CLINIC] {d['clinic']}</div>
          <div style="font-size:12px;color:#555">[TEL] {d['phone']}</div>
          <a href="{d['maps_link']}" target="_blank"
          style="display:inline-block;margin-top:8px;background:#0066cc;color:white;
          padding:4px 12px;border-radius:8px;font-size:11px;text-decoration:none">
          [MAP] View on Maps</a>
        </div>""" for d in doctors
    ]) if doctors else "<p style='color:#888'>No doctors found for this location.</p>"

    doc_html = f"""
    <div style="margin-bottom:14px">
      <div style="font-weight:700;margin-bottom:10px;font-size:15px">[CLINIC] Nearby Dermatologists</div>
      <div style="display:flex;gap:10px;flex-wrap:wrap">{doc_cards}</div>
    </div>
    """

    # History panel
    hist_items = "".join([
        f"""<div style="background:#f0f4f8;border-radius:8px;padding:6px 12px;
        font-size:12px;margin-bottom:4px">
          [TIME] {h['time']} -- <b>{h['label'].capitalize()}</b> ({h['confidence']:.0f}%)
        </div>""" for h in history
    ])
    hist_html = f"""
    <div style="margin-bottom:14px">
      <div style="font-weight:700;margin-bottom:6px">[HISTORY] Recent Predictions (last 5)</div>
      {hist_items}
    </div>
    """

    # Disclaimer
    disclaimer_html = """
    <div style="border-top:1px solid #eee;margin-top:14px;padding-top:10px;
    font-size:11px;color:#888;text-align:center">
      [!] <b>For educational purposes only. Always consult a certified dermatologist.</b>
    </div>
    """

    # Combine everything
    full_html = (
        badge_html + conf_html + top3_html +
        med_html + prec_html + doc_html +
        hist_html + disclaimer_html
    )

    return full_html, pdf_path


# =====================
# BUILD GRADIO LAYOUT
# =====================

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="blue"),
    title="DermIQ",
    css="""
    .gr-button-primary { background: #0066cc !important; }
    footer { display: none !important; }
    body { transition: background-color 0.3s, color 0.3s; }
    .dark-mode { background-color: #121212 !important; color: #ffffff !important; }
    .dark-mode .gr-box { background-color: #1e1e1e !important; border-color: #333 !important; }
    .dark-mode .gr-html { color: #ffffff !important; }
    """
) as demo:

    # Branded header
    gr.HTML("""
    <div style="background:linear-gradient(135deg,#0066cc,#0044aa);
    padding:28px 32px;border-radius:14px;margin-bottom:20px;color:white;position:relative">
      <div style="font-size:32px;font-weight:900;letter-spacing:-1px">
        Derm<span style="color:#3ddbb7">IQ</span>
      </div>
      <div style="font-size:14px;opacity:0.8;margin-top:4px">
        AI-Powered Skin Intelligence
      </div>
      <button id="theme-toggle" style="position:absolute;top:10px;right:10px;background:#fff;color:#0066cc;border:none;padding:5px 10px;border-radius:5px;cursor:pointer">🌙 Dark</button>
    </div>
    <script>
    document.getElementById('theme-toggle').addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        this.textContent = document.body.classList.contains('dark-mode') ? '☀️ Light' : '🌙 Dark';
    });
    </script>
    """)

    # Two-column layout
    with gr.Row():

        # LEFT column — inputs
        with gr.Column(scale=1):
            img_input = gr.Image(
                type="pil",
                label="Upload Skin Image",
            )
            city_input = gr.Textbox(
                placeholder="Enter city name or PIN code",
                label="Find Nearby Doctors"
            )
            submit_btn = gr.Button(
                "ANALYZE SKIN",
                variant="primary",
                elem_id="analyze-btn"
            )
            clear_btn = gr.Button("CLEAR HISTORY", variant="secondary")

        # RIGHT column — results
        with gr.Column(scale=1):
            result_html = gr.HTML(
                value="<p style='color:#aaa;text-align:center;margin-top:40px'>"
                      "Upload an image and click Analyze to see results.</p>"
            )
            pdf_output = gr.File(label="PDF Report")

    # Button actions
    submit_btn.click(
        fn=analyze,
        inputs=[img_input, city_input],
        outputs=[result_html, pdf_output]
    )
    clear_btn.click(
        fn=clear_history,
        inputs=[],
        outputs=[result_html]
    )

demo.launch(show_error=True)