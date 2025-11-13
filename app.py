from flask import Flask, request, send_file, render_template_string
import os
import fitz
import io
from PIL import Image, ImageDraw
import re

app = Flask(__name__)

HTML_FORM = """
<h2>Tarjador de PDF</h2>
<form method="POST" enctype="multipart/form-data">
    <label>Arquivo PDF:</label><br>
    <input type="file" name="pdf" required><br><br>

    <label>Caracteres ignorados (separados por vírgula):</label><br>
    <input type="text" name="ignored" value="-, /, \\, º, :, @" style="width:300px;"><br><br>

    <button type="submit">Processar</button>
</form>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return HTML_FORM

    file = request.files["pdf"]
    ignored = request.form.get("ignored", "")
    ignored_set = set([c.strip() for c in ignored.split(",") if c.strip()])

    pdf_bytes = file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    output_pdf = fitz.open()

    total_trejados = 0

    patterns = [
        r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
        r"\b\d{2}\.\d{3}\.\d{3}-\d{1}\b",
        r"\b\d{7,9}\b"
    ]

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        text = page.get_text("text")

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                encontrado = match.group()

                if any(ch in encontrado for ch in ignored_set):
                    continue

                for rect in page.search_for(encontrado):
                    total_trejados += 1
                    draw = ImageDraw.Draw(img)
                    draw.rectangle([(rect.x0, rect.y0), (rect.x1, rect.y1)], fill="black")

        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PDF")
        temp_doc = fitz.open("pdf", img_bytes.getvalue())
        output_pdf.insert_pdf(temp_doc)

    output_buffer = io.BytesIO()
    output_pdf.save(output_buffer)

    return send_file(
        io.BytesIO(output_buffer.getvalue()),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="tarjado.pdf"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Porta fornecida pelo Railway
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


