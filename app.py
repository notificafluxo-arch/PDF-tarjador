import re
from io import BytesIO
from flask import Flask, request, send_file, render_template_string
from pdf2image import convert_from_path
from PIL import Image, ImageDraw
import pytesseract
import os

app = Flask(__name__)

# Tesseract no Railway será encontrado normalmente
pytesseract.pytesseract.tesseract_cmd = "tesseract"

CPF_REGEX = re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b')
RG_REGEX = re.compile(r'\b([A-Z]{2}-)?\d{1,2}\.?\d{3}\.?\d{3}-?\d?\b', re.IGNORECASE)

def apenas_digitos(s: str) -> str:
    return re.sub(r'\D', '', s or '')

def aplicar_tarjas_na_imagem(img: Image.Image, ignorar_chars: str) -> Image.Image:
    draw = ImageDraw.Draw(img)

    try:
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang='por')
    except Exception:
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    n_boxes = len(data['level'])

    for i in range(n_boxes):
        text = (data['text'][i] or "").strip()
        if not text:
            continue

        if any(ch in text for ch in ignorar_chars):
            continue

        norm = apenas_digitos(text)
        if not norm.isdigit():
            continue

        is_cpf = len(norm) == 11
        is_rg = 7 <= len(norm) <= 9

        if is_cpf or is_rg:
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            margem_x = int(w * 0.10)
            margem_y = int(h * 0.25)
            box = [x - margem_x, y - margem_y, x + w + margem_x, y + h + margem_y]
            draw.rectangle(box, fill="black")

    return img

@app.route("/", methods=["GET", "POST"])
def index():
    html = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Tarjador LGPD</title>
    </head>
    <body style="font-family: Arial; padding: 30px;">
      <h2>Tarjador de CPF / RG (LGPD)</h2>
      <form method="post" enctype="multipart/form-data">
        <p>Selecione um PDF:</p>
        <input type="file" name="file" required><br><br>

        <p>Caracteres a ignorar:</p>
        <input type="text" name="ignorar" value="-,/\\º:@"><br><br>

        <button type="submit">Processar</button>
      </form>
    </body>
    </html>
    """

    if request.method == "POST":
        arquivo = request.files.get("file")
        if not arquivo:
            return "Nenhum arquivo enviado", 400

        ignorar_chars = request.form.get("ignorar", "-,/\\º:@")

        temp_input = "input.pdf"
        arquivo.save(temp_input)

        try:
            images = convert_from_path(temp_input, dpi=300)
        except Exception as e:
            return f"Erro ao converter PDF: {e}", 500

        output_images = []
        for img in images:
            img_rgb = img.convert("RGB")
            img_proc = aplicar_tarjas_na_imagem(img_rgb, ignorar_chars)
            output_images.append(img_proc)

        buffer = BytesIO()
        output_images[0].save(buffer, format="PDF", save_all=True, append_images=output_images[1:])
        buffer.seek(0)

        os.remove(temp_input)

        return send_file(buffer, download_name="tarjado.pdf", as_attachment=True)

    return render_template_string(html)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
