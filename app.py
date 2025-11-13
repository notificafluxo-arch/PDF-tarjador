from flask import Flask, request, send_file, render_template_string
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import re
import os

app = Flask(__name__)

HTML_FORM = """
<h2>Tarjador de PDF (Texto pesquisável)</h2>
<form method="POST" enctype="multipart/form-data">
    <label>Arquivo PDF:</label><br>
    <input type="file" name="pdf" required><br><br>

    <label>Caracteres a ignorar (separados por vírgula):</label><br>
    <input type="text" name="ignored" value="- , / , \\ , º , : , @" style="width:300px;"><br><br>

    <button type="submit">Processar</button>
</form>
<p>Obs: Apenas PDFs com texto pesquisável são suportados. PDFs escaneados não funcionarão.</p>
"""

# Regexs para CPF e RG
CPF_PATTERN = re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b')
RG_PATTERN = re.compile(r'\b\d{7,9}\b')

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return HTML_FORM

    file = request.files["pdf"]
    ignored = request.form.get("ignored", "")
    ignored_set = set([c.strip() for c in ignored.split(",") if c.strip()])

    reader = PdfReader(file)
    writer = PdfWriter()

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text() or ""

        # Overlay PDF
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        # Tarjas CPF
        for match in CPF_PATTERN.finditer(text):
            cpf = match.group()
            if any(c in cpf for c in ignored_set):
                continue
            # Exemplo fixo, ajuste conforme necessidade
            can.setFillColorRGB(0, 0, 0)
            can.rect(100, 700, 150, 15, fill=True, stroke=False)

        # Tarjas RG
        for match in RG_PATTERN.finditer(text):
            rg = match.group()
            if any(c in rg for c in ignored_set):
                continue
            can.setFillColorRGB(0, 0, 0)
            can.rect(100, 680, 100, 15, fill=True, stroke=False)

        can.save()
        packet.seek(0)

        overlay = PdfReader(packet)
        page.merge_page(overlay.pages[0])
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="tarjado.pdf",
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
