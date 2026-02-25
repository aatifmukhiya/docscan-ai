# DocScan AI 🔍

> **Smart Document Scanner & OCR Field Extractor**  
> Upload any invoice, receipt, or document — get text + structured fields extracted automatically.  
> Supports **Images** (PNG, JPG, JPEG) and **PDF** files.

---

## ✨ Features

-  **PDF Support** — Upload PDFs directly; first page is auto-converted and scanned
-  **Smart Field Extraction** — Auto-detects Invoice No, Date, Total, Customer, Vendor, Email, Phone, Tax, Subtotal, Due Date
-  **4 OCR Modes** — Auto Detect, Invoice, Receipt, Handwritten (each uses different preprocessing)
-  **8 Languages** — English, Hindi, French, German, Spanish, Chinese, Arabic, Japanese
-  **Confidence Score** — Shows OCR accuracy % with a visual progress bar
- ⬇ **Export Results** — Download as `.txt`, `.json`, or `.csv`
-  **Privacy First** — Uploaded files are deleted immediately after processing
-  **Drag & Drop** — Modern dark UI with drag-and-drop file upload

---

## 🖥️ Tech Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Backend | Python | 3.11+ | Main language |
| Backend | Flask | 3.0.3 | Web framework & API routes |
| Backend | Pytesseract | 0.3.13 | Python wrapper for Tesseract |
| Backend | Tesseract OCR | 5.x | OCR engine — reads text from images |
| Backend | Pillow | 10.4.0 | Image preprocessing (contrast, sharpening) |
| Backend | pdf2image | 1.17.0 | Converts PDF pages to images |
| Backend | Poppler | 25.12.0 | PDF rendering engine (used by pdf2image) |
| Backend | Werkzeug | 3.0.3 | Secure file upload handling |
| Frontend | HTML + CSS | — | Dark green hacker theme UI |
| Frontend | Vanilla JS | — | Fetch API, drag & drop, clipboard, downloads |
| Frontend | Google Fonts | — | Syne, IBM Plex Mono, Lora |

---

## 📁 Project Structure

```
docscan-ai/
│
├── app.py                  ← Flask backend (OCR, PDF support, field extraction)
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
├── .gitignore              ← Git ignore rules
│
├── templates/
│   └── index.html          ← Frontend UI (drag & drop, field cards, exports)
│
└── uploads/
    └── .gitkeep            ← Keeps uploads/ folder in Git (files are gitignored)
```

---

## ⚙️ Installation Guide (Windows)

### Prerequisites

Before running the app, install these 3 tools:

---

### Step 1 — Install Python 3.11

1. Go to: https://python.org/downloads
2. Download Python **3.11.x** (avoid 3.14 — compatibility issues)
3. Run installer — **tick "Add Python to PATH"** before clicking Install
4. Verify:
```bash
python --version
# Expected: Python 3.11.x
```

---

### Step 2 — Install Tesseract OCR

1. Go to: https://github.com/UB-Mannheim/tesseract/wiki
2. Download the Windows installer (`.exe`)
3. Install to default path: `C:\Program Files\Tesseract-OCR\`
4. During install, select extra languages if needed (Hindi, etc.)
5. Verify:
```bash
"C:\Program Files\Tesseract-OCR\tesseract.exe" --version
```

---

### Step 3 — Install Poppler (for PDF support)

1. Go to: https://github.com/oschwartz10612/poppler-windows/releases
2. Download latest `.zip` (e.g., `poppler-25.12.0_x86.zip`)
3. Extract the zip
4. Move the folder to: `C:\Users\YOUR_USERNAME\poppler-25.12.0\`
5. Verify:
```bash
dir "C:\Users\YOUR_USERNAME\poppler-25.12.0\Library\bin\pdftoppm.exe"
# Mode should show -a---- (not ------)
```

> ⚠️ **If Mode shows `------` (no permissions):** Run this to fix:
> ```bash
> icacls "C:\Users\YOUR_USERNAME\poppler-25.12.0" /grant YOUR_USERNAME:F /T
> ```

---

### Step 4 — Install Visual C++ Redistributable

> ⚠️ **Required for Poppler to work on Windows.** Without it, PDF conversion fails with error code `3221225781`.

1. Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
2. Run the installer → click Install
3. **Restart your computer** after installation

---

### Step 5 — Clone / Download the Project

```bash
# Option A: Clone from GitHub
git clone https://github.com/YOUR_USERNAME/docscan-ai.git
cd docscan-ai

# Option B: Download ZIP from GitHub and extract to Desktop
cd C:\Users\YOUR_USERNAME\Desktop\docscan-ai
```

---

### Step 6 — Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate it (run this EVERY TIME you open a new terminal)
.\venv\Scripts\Activate.ps1
```

> ⚠️ **If activation fails** with "cannot be loaded" error:
> ```bash
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> # Press Y then Enter
> .\venv\Scripts\Activate.ps1
> ```

You should now see `(venv)` at the start of your terminal line. ✅

---

### Step 7 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

Verify pdf2image installed:
```bash
python -c "from pdf2image import convert_from_path; print('pdf2image OK!')"
# Expected output: pdf2image OK!
```

---

### Step 8 — Update Paths in app.py

Open `app.py` and update these 2 lines:

```python
# Line 8 — Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Line 17 — Poppler path (change YOUR_USERNAME)
POPPLER_PATH = r'C:\Users\YOUR_USERNAME\poppler-25.12.0\Library\bin'
```

---

### Step 9 — Run the App

```bash
python app.py
```

Expected output:
```
====================================================
  DocScan AI v3.0 — Starting...
  Open: http://127.0.0.1:5000
====================================================
```

Open your browser and go to: **http://127.0.0.1:5000** 🎉

---

## 🧠 How It Works

```
User uploads file (Image or PDF)
        ↓
Flask saves file temporarily with a random UUID filename
        ↓
open_file()
  ├── PDF?   → pdf2image converts page 1 to PIL Image using Poppler
  └── Image? → Pillow opens directly
        ↓
preprocess_image()
  ├── Invoice  → Grayscale + 2.0x contrast + sharpening
  ├── Receipt  → Grayscale + 2.5x contrast + 2.0x sharpening
  ├── Handwritten → Grayscale + SHARPEN filter
  └── Auto    → Grayscale + 1.5x contrast
        ↓
Tesseract OCR → extracts raw text + confidence scores per word
        ↓
extract_fields() → regex finds Invoice No, Date, Amount, etc.
        ↓
JSON response sent to browser → UI displays field cards + stats
        ↓
Uploaded file DELETED from server immediately
```

---

## 📋 Smart Field Extraction

The app automatically detects and extracts these 10 fields:

| Field | Example | How Detected |
|-------|---------|-------------|
| Invoice Number | INV-2024-001 | Keywords: INVOICE, INV, BILL, ORDER + alphanumeric |
| Date | 15/01/2024 | Formats: DD/MM/YYYY, YYYY-MM-DD, Jan 15 2024 |
| Due Date | 30/01/2024 | Keywords: DUE DATE, PAYMENT DUE, PAY BY + date |
| Total Amount | ₹5,250.00 | Scans from bottom: TOTAL, GRAND TOTAL, AMOUNT DUE |
| Subtotal | ₹4,500.00 | Keyword: SUBTOTAL near a number |
| Tax / GST | ₹750.00 | Keywords: TAX, VAT, GST, HST near a number |
| Customer Name | Aatif Khan | Line after: BILL TO, BILLED TO, CUSTOMER, CLIENT |
| Vendor | XYZ Company | Line after: FROM, VENDOR, SELLER, COMPANY |
| Email | info@xyz.com | Standard email regex pattern |
| Phone | +91 9876543210 | Phone label + 7-16 digit sequence |

---

## 🌍 Supported Languages

| Language | Code | Tesseract Package |
|----------|------|------------------|
| English | `eng` | Included by default |
| Hindi | `hin` | tesseract-ocr-hin |
| French | `fra` | tesseract-ocr-fra |
| German | `deu` | tesseract-ocr-deu |
| Spanish | `spa` | tesseract-ocr-spa |
| Chinese (Simplified) | `chi_sim` | tesseract-ocr-chi-sim |
| Arabic | `ara` | tesseract-ocr-ara |
| Japanese | `jpn` | tesseract-ocr-jpn |

---

## 🔌 API Reference

### `GET /`
Returns the main HTML page.

---

### `POST /ocr`
Accepts a document and returns extracted text + fields.

**Request** (`multipart/form-data`):

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | ✅ Yes | Image or PDF file |
| `lang` | String | No | Language code (default: `eng`) |
| `mode` | String | No | OCR mode (default: `auto`) |

**Response** (JSON):
```json
{
  "text": "INVOICE\nInvoice No: INV-001\nDate: 15/01/2024...",
  "confidence": 87.4,
  "word_count": 142,
  "char_count": 856,
  "mode": "invoice",
  "lang": "eng",
  "fields": {
    "invoice_number": "INV-001",
    "date": "15/01/2024",
    "due_date": "30/01/2024",
    "total_amount": "5250.00",
    "subtotal": "4500.00",
    "tax": "750.00",
    "customer_name": "Aatif Khan",
    "vendor": "XYZ Company Pvt Ltd",
    "email": "info@xyz.com",
    "phone": "+91 9876543210",
    "detected_type": "Invoice"
  }
}
```

---

## 🐛 Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `tesseract is not installed` | Tesseract not found | Install from UB-Mannheim and check path in app.py line 8 |
| `0% confidence / no text` | Wrong Tesseract path | Update `tesseract_cmd` in app.py |
| `PDF conversion failed: Unable to get page count` | Wrong Poppler path | Update `POPPLER_PATH` in app.py |
| Return code `3221225781` | Missing Visual C++ DLL | Install from https://aka.ms/vs/17/release/vc_redist.x64.exe then restart PC |
| `venv module could not be loaded` | venv not created yet | Run `python -m venv venv` first |
| `Activate.ps1 cannot be loaded` | PowerShell policy | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `pdf2image not installed` | Not in venv | Run `pip install pdf2image` with venv active |
| `TemplateNotFound: index.html` | Wrong folder | Make sure `index.html` is inside `templates/` folder |
| Port 5000 already in use | Another app running | Change port: `app.run(port=5001)` in app.py |

---

## 🚀 GitHub Upload

### First Time
```bash
cd C:\Users\YOUR_USERNAME\Desktop\docscan-ai
git init
git add .
git commit -m "Initial commit: DocScan AI v3.0"
git remote add origin https://github.com/YOUR_USERNAME/docscan-ai.git
git branch -M main
git push -u origin main
```

### After Every Update
```bash
git add .
git commit -m "Describe your change here"
git push
```

### What Gets Uploaded vs Ignored

| File / Folder | Uploaded? | Reason |
|--------------|-----------|--------|
| `app.py` | ✅ Yes | Main code |
| `templates/index.html` | ✅ Yes | Frontend |
| `requirements.txt` | ✅ Yes | Dependencies |
| `README.md` | ✅ Yes | Docs |
| `.gitignore` | ✅ Yes | Git rules |
| `venv/` | ❌ No | Too large — everyone creates their own |
| `uploads/*` | ❌ No | User files (privacy) |
| `__pycache__/` | ❌ No | Python cache |
| Poppler folder | ❌ No | Must be installed locally |

---

## 💡 Daily Commands (Quick Reference)

```bash
# 1. Go to project
cd C:\Users\YOUR_USERNAME\Desktop\docscan-ai

# 2. Activate venv (do this EVERY TIME)
.\venv\Scripts\Activate.ps1

# 3. Run app
python app.py

# 4. Open browser
# http://127.0.0.1:5000

# 5. Stop app
# Ctrl + C
```

---

## 📌 Important Paths

```
Tesseract EXE:  C:\Program Files\Tesseract-OCR\tesseract.exe
Poppler bin:    C:\Users\YOUR_USERNAME\poppler-25.12.0\Library\bin\
Project folder: C:\Users\YOUR_USERNAME\Desktop\docscan-ai\
Virtual env:    C:\Users\YOUR_USERNAME\Desktop\docscan-ai\venv\
App URL:        http://127.0.0.1:5000
```

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*DocScan AI v3.0 · Built with Python, Flask, Tesseract OCR, pdf2image & Poppler*