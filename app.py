from flask import Flask, request, jsonify, render_template
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import os
import uuid
import re
from werkzeug.utils import secure_filename

# ✅ Windows fix — Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ✅ PDF support
try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Poppler path for Windows (required for PDF conversion)
POPPLER_PATH = r'C:\Users\AATIF\poppler-25.12.0\Library\bin'

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max
app.config['UPLOAD_FOLDER'] = 'uploads'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif', 'webp', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def open_file(filepath):
    ext = filepath.rsplit('.', 1)[-1].lower()
    if ext == 'pdf':
        if not PDF_SUPPORT:
            raise Exception("PDF support not installed. Run: pip install pdf2image")
        try:
            pages = convert_from_path(filepath, dpi=200, poppler_path=POPPLER_PATH)
            if not pages:
                raise Exception("PDF has no pages or could not be read.")
            return pages[0]
        except Exception as e:
            raise Exception(f"PDF conversion failed: {str(e)}\nMake sure Poppler is installed at: {POPPLER_PATH}")
    else:
        return Image.open(filepath)


def preprocess_image(image, mode):
    if mode == 'receipt':
        image = image.convert('L')
        image = ImageEnhance.Contrast(image).enhance(2.5)
        image = ImageEnhance.Sharpness(image).enhance(2.0)
    elif mode == 'invoice':
        image = image.convert('L')
        image = ImageEnhance.Contrast(image).enhance(2.0)
        image = ImageEnhance.Sharpness(image).enhance(1.5)
    elif mode == 'handwritten':
        image = image.convert('L')
        image = image.filter(ImageFilter.SHARPEN)
    else:
        image = image.convert('L')
        image = ImageEnhance.Contrast(image).enhance(1.5)
    return image


def extract_fields(text):
    fields = {}
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Invoice / Receipt Number
    inv_patterns = [
        r'(?:INVOICE|INV|RECEIPT|BILL|ORDER)[^\d#\n]*[#№]?\s*:?\s*([A-Z0-9][-A-Z0-9/]{2,20})',
        r'\b(INV[-/]?\d{3,12})\b',
        r'\b(BILL[-/]?\d{3,12})\b',
        r'(?:NO|NUMBER|#)[.:\s]*([A-Z0-9\-/]{4,20})',
    ]
    for pat in inv_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            fields['invoice_number'] = m.group(1).strip()
            break

    # Receipt No fallback
    if 'invoice_number' not in fields:
        receipt = re.search(r'(?:Receipt\s*No|Receipt\s*Number)\s*[:\-]?\s*([A-Z0-9][\w\-]{3,20})', text, re.IGNORECASE)
        if receipt:
            fields['invoice_number'] = receipt.group(1).strip()

    # Date
    date_patterns = [
        r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b',
        r'\b(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})\b',
        r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4})\b',
        r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b',
    ]
    date_context = ['date', 'dated', 'issued', 'invoice date', 'bill date']
    for i, line in enumerate(lines):
        if any(ctx in line.lower() for ctx in date_context):
            block = ' '.join(lines[max(0, i - 1):i + 3])
            for pat in date_patterns:
                m = re.search(pat, block, re.IGNORECASE)
                if m:
                    fields['date'] = m.group(1).strip()
                    break
        if 'date' in fields:
            break
    if 'date' not in fields:
        for pat in date_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                fields['date'] = m.group(1).strip()
                break

    # Due Date
    due = re.search(r'(?:DUE\s+DATE|PAYMENT\s+DUE|PAY\s+BY)[^\d\n]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})', text, re.IGNORECASE)
    if due:
        fields['due_date'] = due.group(1).strip()

    # Total Amount
    total_patterns = [
        r'(?:GRAND\s+TOTAL|TOTAL\s+AMOUNT|AMOUNT\s+DUE|AMOUNT\s+PAYABLE|NET\s+AMOUNT|BALANCE\s+DUE|TOTAL)[^\d$£€₹\n]{0,20}[$£€₹]?\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?)',
        r'[$£€₹]\s*(\d{1,3}(?:[,\s]\d{3})*\.\d{2})\s*$',
    ]
    for line in reversed(lines):
        for pat in total_patterns:
            m = re.search(pat, line, re.IGNORECASE)
            if m:
                currency = ''
                cm = re.search(r'[$£€₹]', line)
                if cm:
                    currency = cm.group()
                fields['total_amount'] = currency + m.group(1).strip()
                break
        if 'total_amount' in fields:
            break

    # Subtotal
    sub = re.search(r'(?:SUB[\s\-]?TOTAL)[^\d$£€₹\n]*[$£€₹]?\s*(\d[\d,\.]+)', text, re.IGNORECASE)
    if sub:
        fields['subtotal'] = sub.group(1).strip()

    # Tax
    tax = re.search(r'(?:TAX|VAT|GST|HST)[^\d$£€₹\n%]*[\d.]*%?[^\d$£€₹\n]*[$£€₹]?\s*(\d[\d,\.]+)', text, re.IGNORECASE)
    if tax:
        fields['tax'] = tax.group(1).strip()

    # ── Customer Name ─────────────────────────────────────────
    # Pattern 1: "Name : JACHWEL RONGPHER" same line
    name_inline = re.search(
        r'(?:^|\n)\s*(?:Name|Nome|Nam|Customer\s*Name|Consumer\s*Name|Account\s*Name|Account\s*Holder)\s*[:\-]\s*([A-Za-z][A-Za-z\s\.]{2,40})',
        text, re.IGNORECASE | re.MULTILINE
    )
    if name_inline:
        raw = name_inline.group(1).strip()
        # ✅ Trim trailing garbage words OCR picks up after name
        raw = re.split(
            r'\s+(?:Bill|Amount|Due|Date|Payment|Invoice|No|Receipt|Total|Mode|Cash|Rs|Rupees)',
            raw, flags=re.IGNORECASE
        )[0]
        fields['customer_name'] = raw.strip()

    # Pattern 2: keyword triggers next line search
    if 'customer_name' not in fields:
        customer_triggers = ['bill to', 'billed to', 'customer', 'client', 'sold to', 'ship to', 'consumer', 'account holder']
        for i, line in enumerate(lines):
            if any(t in line.lower() for t in customer_triggers):
                same_line = re.search(r'[:\-]\s*([A-Za-z][A-Za-z\s\.]{2,40})$', line)
                if same_line:
                    fields['customer_name'] = same_line.group(1).strip()
                    break
                for j in range(i + 1, min(i + 4, len(lines))):
                    c = lines[j].strip()
                    if c and not re.match(r'^\d+', c) and len(c) > 2:
                        if not any(s in c.lower() for s in ['invoice', 'date', 'total', 'tax', 'amount', 'mode']):
                            fields['customer_name'] = c
                            break
                break

    # Consumer No
    consumer = re.search(r'(?:Consumer\s*No|Consumer\s*Number|Account\s*No|Account\s*Number)\s*[:\-]?\s*(\d{5,20})', text, re.IGNORECASE)
    if consumer:
        fields['consumer_no'] = consumer.group(1).strip()

    # Vendor
    vendor_triggers = ['from:', 'vendor', 'company', 'seller', 'supplier']
    for i, line in enumerate(lines):
        if any(t in line.lower() for t in vendor_triggers):
            for j in range(i + 1, min(i + 3, len(lines))):
                c = lines[j].strip()
                if c and len(c) > 2:
                    fields['vendor'] = c
                    break
            break
    if 'vendor' not in fields and lines:
        first = lines[0]
        if len(first) > 2 and not any(s in first.lower() for s in ['invoice', 'receipt', 'bill', 'page']):
            fields['vendor'] = first

    # Email
    email = re.search(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b', text)
    if email:
        fields['email'] = email.group()

    # Phone
    phone = re.search(r'(?:Tel|Phone|Ph|Mobile|Contact)?[:\s]*(\+?[\d\s\-().]{7,16}\d)', text, re.IGNORECASE)
    if phone:
        p = re.sub(r'\s+', ' ', phone.group(1)).strip()
        if len(re.sub(r'\D', '', p)) >= 7:
            fields['phone'] = p

    # Document Type
    doc_map = {
        'Invoice':        ['invoice', 'tax invoice', 'proforma'],
        'Receipt':        ['receipt', 'payment received', 'thank you for'],
        'Purchase Order': ['purchase order', 'p.o.', 'po#'],
        'ID Card':        ['date of birth', 'dob', 'licence', 'license'],
        'Medical':        ['patient', 'prescription', 'doctor', 'clinic'],
        'Bank Statement': ['transaction', 'debit', 'credit', 'account no'],
        'Contract':       ['agreement', 'terms and conditions', 'hereby'],
    }
    fields['detected_type'] = 'General Document'
    for dtype, keywords in doc_map.items():
        if any(kw in text.lower() for kw in keywords):
            fields['detected_type'] = dtype
            break

    return fields


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ocr', methods=['POST'])
def ocr():
    if 'image' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['image']
    lang = request.form.get('lang', 'eng')
    mode = request.form.get('mode', 'auto')

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Use PNG, JPG, BMP, TIFF, or PDF.'}), 400

    filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        image = open_file(filepath)
        image = preprocess_image(image, mode)

        psm_map = {'auto': 3, 'handwritten': 13, 'receipt': 6, 'invoice': 6}
        psm    = psm_map.get(mode, 3)
        config = f'--psm {psm} --oem 3'

        raw_text = pytesseract.image_to_string(image, lang=lang, config=config)

        data = pytesseract.image_to_data(image, lang=lang, config=config, output_type=pytesseract.Output.DICT)
        confidences = [int(c) for c in data['conf'] if str(c) != '-1' and int(c) > 0]
        avg_conf    = round(sum(confidences) / len(confidences), 1) if confidences else 0
        word_count  = len([w for w in data['text'] if w.strip()])

        fields = extract_fields(raw_text)

        return jsonify({
            'text':       raw_text.strip(),
            'fields':     fields,
            'confidence': avg_conf,
            'word_count': word_count,
            'char_count': len(raw_text.strip()),
            'mode':       mode,
            'lang':       lang
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run()