import cv2
import pytesseract

# Carregando a imagem do documento
imagem_documento_path = 'imagens/NFSe_ficticia.jpg'
imagem_documento = cv2.imread(imagem_documento_path)

# Convertendo a imagem para escala de cinza
imagem_documento_cinza = cv2.cvtColor(imagem_documento, cv2.COLOR_BGR2GRAY)

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