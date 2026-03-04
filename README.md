# DermIQ
AI-Powered Skin Concern Classifier using Transfer Learning

## ✅ UI/UX Features Implemented
- Gradio frontend with custom `Soft` theme and blue/white palette
- Two‑column layout: image upload on the left, results on the right
- Branded header with DermIQ logo text, tagline and **dark/light mode toggle**
- Confidence score progress bar and **severity badge** (color coded)
- Top‑3 probability display as inline bars
- Medication recommendation card with warnings and usage instructions
- Precaution tips section populated by condition
- Nearby dermatologist suggestions (city/PIN input) with Google Maps links
- Prediction history panel (last 5) with clear history button
- PDF report export using `fpdf2` saved to `/reports` with timestamp filename
- Dark/light mode support via simple JS toggle and CSS adjustments
- Loading spinner/message during prediction (Gradio default)
- Responsive layout (works on mobile widths)
- Medical disclaimer at bottom of results

## 🛠️ Testing & Validation
Run the standalone script to verify the full flow and PDF generation:

```sh
python test_standalone.py
```

Generated PDFs are placed in `reports/` and copied to `test_results/`.

## 📁 Repository Notes
- `reports/` is included in `.gitignore` so PDFs aren’t committed
- Requirements already include `fpdf2` for PDF support

## 🚀 Getting Started
1. Create and activate the virtual environment:
   ```sh
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```
2. Launch the Gradio app:
   ```sh
   python app.py
   ```
3. Upload a skin image, enter a city or PIN, and click **ANALYZE SKIN**.
4. Download the PDF report if desired and view predicted results.

---

Feel free to adapt this checklist into Notion or any project management tool.
