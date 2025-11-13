import os
import fitz  # PyMuPDF
from flask import Flask, render_template, request, send_file

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/tarjar", methods=["POST"])
def tarjar_pdf():
    if "pdf" not in request.files:
        return "Nenhum PDF enviado", 400

    uploaded_pdf = request.files["pdf"]

    # Railway só permite escrita em /tmp
    input_path = "/tmp/input.pdf"
    output_path = "/tmp/output.pdf"

    uploaded_pdf.save(input_path)

    # Abre PDF
    doc = fitz.open(input_path)

    # Exemplo de tarja simples (preta)
    for page in doc:
        rect = fitz.Rect(50, 50, 500, 120)  # ajuste conforme desejar
        page.draw_rect(rect, color=(0, 0, 0), fill=(0, 0, 0))

    # Salva PDF final
    doc.save(output_path)
    doc.close()

    # Retorna o PDF ao usuário
    return send_file(output_path, as_attachment=True, download_name="tarjado.pdf")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
