import pytesseract
import cv2
import re

from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  

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
        caminhos = [f"{caminho[:-4]}.jpg"]
elif caminho[-4:] ==".jpg" or caminho[-4:] ==".png":
    caminhos = [caminho]

texto_completo = ""
for img_path in caminhos:
    # print(caminhos)
    print(f"Processando imagem: {img_path}")
    imagem = cv2.imread(img_path)

    # Verifica se a imagem carregou corretamente
    if imagem is not None:
        # Redimensiona para o dobro do tamanho (2x)
        # fx=2, fy=2: Fatores de escala horizontal e vertical
        # interpolation=cv2.INTER_CUBIC: Melhor algoritmo para qualidade ao aumentar
        imagem_grande = cv2.resize(imagem, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # Exemplo: Mostrar a imagem resultante (pressione 0 para ir para a próxima)
        # cv2.imshow("Imagem Ampliada", imagem_grande)
        # cv2.waitKey(0) 
        # cv2.destroyAllWindows()
    else:
        print(f"Erro ao carregar: {img_path}")

    # Pré-processamento
    imagem_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    
    # Binarização com Otsu (Geralmente melhor que valor fixo 128)
    _, imagem_binaria = cv2.threshold(imagem_cinza, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # OCR
    # --psm 3 é o padrão (Fully automatic page segmentation)
    texto_pagina = pytesseract.image_to_string(imagem_binaria, lang='por+eng', config='--psm 3 --psm 6')
    texto_completo += texto_pagina + "\n"

# Imprimindo o texto detectado
# print(f'Texto Detectado: {texto_completo}')

import re
import json

# --- CONFIGURAÇÕES ---
padroes = {
    # Nota: Coloquei todos como listas para facilitar o loop, mesmo os que tinham um só
    "cnpj": [r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"], 
    "cpf": [r"\d{3}\.\d{3}\.\d{3}-\d{2}"],
    "email": [r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"],
    "telefone": [r"\(?\d{2}\)?\s*?\d{4,5}-?\d{4}"],
    "nf-e": [r'\b(?:\d[\s.]*){44}\b']
}

palavras_secao = {
    "prestador": ["prestador", "emitente"],
    "tomador": ["tomador", "destinatário", "cliente"]
}

palavras_campos = {
    "razao_social": ["razão social", "nome/razão social", "nome do prestador", "nome fantasia", "nome social", "nome"],
    "endereco": ["endereço", "logradouro", "localização"]
}

dados_extraidos = {
    "prestador": {},
    "tomador": {}
}

# Funções Auxiliares
def adicionar_dado(contexto, chave, valor):
    if chave not in dados_extraidos[contexto]:
        dados_extraidos[contexto][chave] = []
    if valor and valor not in dados_extraidos[contexto][chave]:
        dados_extraidos[contexto][chave].append(valor)

def limpar_e_extrair(linha, chave_detectada):
    """
    Remove tudo que vem ANTES da chave detectada na linha.
    Ex: 'Município: SP Endereço: Rua A' -> Detecta 'Endereço' -> Retorna 'Rua A'
    """
    pattern = rf".*?{chave_detectada}[:\s]*"
    # count=1 garante que removemos apenas a primeira ocorrência (o prefixo)
    valor = re.sub(pattern, "", linha, count=1, flags=re.IGNORECASE).strip()
    return valor
            
# --- PROCESSAMENTO ---

contexto_atual = None 
texto_separado = texto_completo.split('\n')

for linha in texto_separado:
    linha_limpa = linha.strip()
    linha_lower = linha.lower()
    
    if not linha_limpa:
        continue

    # 1. Identificar Contexto (Prestador ou Tomador)
    if any(k in linha_lower for k in palavras_secao["prestador"]):
        contexto_atual = "prestador"
    elif any(k in linha_lower for k in palavras_secao["tomador"]):
        # print(linha_limpa)
        contexto_atual = "tomador"

    if contexto_atual is None:
        continue

    # 2. Extração via Regex (CNPJ, Email, Tel) - Padrões que não dependem de chave:valor
    for tipo_dado, lista_regex in padroes.items():
        for regex in lista_regex:
            encontrados = re.findall(regex, linha_lower)
            # print(encontrados, linha_limpa)
            for item in encontrados:
                adicionar_dado(contexto_atual, tipo_dado, item)

    # 3. Extração de Campos de Texto (Razão Social / Endereço)
    
    # --- RAZÃO SOCIAL ---
    for key in palavras_campos["razao_social"]:
        # print(linha_limpa, key)
        if key in linha_lower:
            # print(key)
            valor = limpar_e_extrair(linha_limpa, key)
            # Verifica se sobrou algo e se não é apenas caracteres especiais soltos
            if valor and len(valor) > 1: 
                adicionar_dado(contexto_atual, "razao_social", valor)
            break # Achou a chave nesta linha, para de testar outras chaves de nome

    # --- ENDEREÇO ---
    for key in palavras_campos["endereco"]:
        if key in linha_lower:
            valor = limpar_e_extrair(linha_limpa, key)
            if valor and len(valor) > 1:
                adicionar_dado(contexto_atual, "endereco", valor)
            break

# --- RESULTADO ---
print(json.dumps(dados_extraidos, indent=4, ensure_ascii=False))