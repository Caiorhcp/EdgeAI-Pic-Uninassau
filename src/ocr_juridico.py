# src/ocr_juridico.py
import os
import io
import pytesseract
from PIL import Image

# Caminho padrão do Tesseract no Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def pdf_para_imagens(arquivo_pdf, dpi=300):
    """
    Converte cada página do PDF em imagem PIL.
    dpi=300 é o mínimo recomendado para OCR jurídico.
    """
    from pdf2image import convert_from_bytes
    if hasattr(arquivo_pdf, "read"):
        dados = arquivo_pdf.read()
        arquivo_pdf.seek(0)
    else:
        with open(arquivo_pdf, "rb") as f:
            dados = f.read()
    return convert_from_bytes(dados, dpi=dpi)

def ocr_pagina(imagem: Image.Image, lang="por") -> str:
    """
    Aplica OCR em uma imagem e retorna o texto extraído.
    lang='por' = português (requer pacote instalado no Tesseract)
    """
    config = "--oem 3 --psm 6"   # oem 3 = LSTM, psm 6 = bloco uniforme de texto
    return pytesseract.image_to_string(imagem, lang=lang, config=config)

def extrair_texto_ocr(arquivo_pdf, dpi=300, lang="por") -> dict:
    """
    Extrai texto de PDF escaneado via OCR.
    Retorna dict com texto por página e texto completo.
    """
    print(f"Convertendo PDF para imagens (DPI={dpi})...")
    imagens = pdf_para_imagens(arquivo_pdf, dpi=dpi)

    paginas = []
    texto_total = []

    for i, imagem in enumerate(imagens):
        print(f"  OCR página {i+1}/{len(imagens)}...")
        texto = ocr_pagina(imagem, lang=lang)
        texto_limpo = texto.strip()
        paginas.append({
            "pagina": i + 1,
            "texto":  texto_limpo,
            "chars":  len(texto_limpo),
        })
        if texto_limpo:
            texto_total.append(f"[Página {i+1}]\n{texto_limpo}")

    return {
        "paginas":      paginas,
        "texto_completo": "\n\n".join(texto_total),
        "total_paginas":  len(imagens),
        "paginas_com_texto": sum(1 for p in paginas if p["chars"] > 20),
    }

def detectar_tipo_pdf(arquivo_pdf) -> str:
    """
    Detecta automaticamente se o PDF é digital ou escaneado.
    Retorna 'digital' ou 'escaneado'.
    """
    import pdfplumber
    with pdfplumber.open(arquivo_pdf) as pdf:
        chars_total = 0
        paginas_testadas = min(3, len(pdf.pages))
        for pag in pdf.pages[:paginas_testadas]:
            t = pag.extract_text()
            if t:
                chars_total += len(t)
    # Se menos de 50 chars por página, provavelmente escaneado
    media = chars_total / paginas_testadas if paginas_testadas > 0 else 0
    return "digital" if media >= 50 else "escaneado"


# ─── Teste standalone ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testando OCR com imagem sintética...")

    # Cria imagem de teste com texto jurídico
    from PIL import ImageDraw, ImageFont
    img = Image.new("RGB", (800, 400), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((50, 50),
        "ACORDAO - STJ, 3a Turma\n"
        "CPF 123.456.789-09\n"
        "Recurso Especial negado por unanimidade.\n"
        "Lei 13.709/2018 - LGPD\n"
        "Valor: R$ 50.000,00",
        fill="black"
    )

    texto = pytesseract.image_to_string(img, lang="por")
    print("Texto extraído via OCR:")
    print(texto)
    print("\nOCR funcionando corretamente!")