import cv2
import pytesseract

import pytesseract
import cv2
import re

from pdf2image import convert_from_path

caminho = 'imagens/NFSe_ficticia_layout_completo.pdf'

if caminho[-4:] == ".pdf":
    pages = convert_from_path(caminho)
    if len(pages) > 1:
        caminhos = []
        for i in range(len(pages)):
            pages[i].save(f"{caminho[:-4]}{str(i)}.jpg", 'JPEG')
            caminhos.append(f"{caminho[:-4]}{str(i)}.jpg")
    else:
        pages[0].save(f"{caminho[:-4]}.jpg", 'JPEG')
        caminhos = f"{caminho[:-4]}.jpg"
elif caminho[-4:] ==".jpg" or caminho[-4:] ==".png":
    caminhos = caminho

# Carregando a imagem
imagem_path = caminhos  # Substitua pelo caminho da sua imagem
imagem = cv2.imread(imagem_path)

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  

# Convertendo a imagem para escala de cinza
imagem_documento_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)

# Aplicando binarização (thresholding)
_, imagem_documento_binaria = cv2.threshold(imagem_documento_cinza, 128, 255, cv2.THRESH_BINARY)

# Aplicando um filtro para remover ruídos (opcional)
imagem_sem_ruido = cv2.medianBlur(imagem_documento_binaria, 1)

# Ajustando o contraste (opcional)
alpha = 1.5  # Fator de contraste
beta = 50    # Fator de brilho
imagem_processada = cv2.convertScaleAbs(imagem_sem_ruido, alpha=alpha, beta=beta)

# Aplicando OCR na imagem do documento
texto_documento = pytesseract.image_to_string(imagem_processada, lang='por')

print(f'Texto no Documento: {texto_documento}')