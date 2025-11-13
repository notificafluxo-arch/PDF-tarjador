from flask import Flask, request, send_file
import fitz
import io
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

    # Carrega PDF
    pdf_bytes = file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    total_trejados = 0

    # Regex CPF e RG
    patterns = [
        r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",   # CPF
        r"\b\d{2}\.\d{3}\.\d{3}-\d{1}\b",   # RG com pontos
        r"\b\d{7,9}\b"                      # RG simples
    ]

    for page in doc:
        text = page.get_text("text")

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                encontrado = match.group()

                # ignorar se tiver caractere proibido
                if any(ch in encontrado for ch in ignored_set):
                    continue

                # encontra coordenadas do texto
                areas = page.search_for(encontrado)

                for rect in areas:
                    total_trejados += 1
                    # desenha tarja preta
                    page.add_rect_annot(rect).update()

    # salva PDF final
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="tarjado.pdf"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
