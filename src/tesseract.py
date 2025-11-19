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
    print(caminhos)
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
    texto_pagina = pytesseract.image_to_string(imagem_binaria, lang='por+eng', config='--psm 3')
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
    # O segundo padrão de email estava redundante com o primeiro, simplifiquei para um genérico
    "email": [r"[\w\.-]+@[\w\.-]+\.\w+"], 
    "telefone": [r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}"]
}

palavras_secao = {
    "prestador": ["prestador", "emitente"],
    "tomador": ["tomador", "destinatário", "cliente"]
}

palavras_campos = {
    "razao_social": ["razão social", "nome/razão social", "nome do prestador", "nome social", "nome"],
    "endereco": ["endereço", "logradouro", "localização"]
}

dados_extraidos = {
    "prestador": {},
    "tomador": {}
}

# Função auxiliar de limpeza baseada no seu pedido
def limpar_valor(linha, chave_detectada):
    # SE TIVER DOIS PONTOS: Pega tudo depois do primeiro ":"
    if ":" in linha:
        # split(':', 1) divide apenas na primeira ocorrência. [1] pega a parte da direita.
        return linha.split(":", 1)[1].strip()
    
    # SE NÃO TIVER DOIS PONTOS: Remove apenas a palavra-chave encontrada
    else:
        # rf"" para raw string (evita warning)
        return re.sub(rf"{chave_detectada}\s*", "", linha, flags=re.IGNORECASE).strip()

# Função auxiliar para adicionar dados em lista sem repetir código
def adicionar_dado(contexto, chave, valor):
    # Se a chave (ex: 'email') ainda não existe no dicionário, cria uma lista vazia
    if chave not in dados_extraidos[contexto]:
        dados_extraidos[contexto][chave] = []
    
    # Evita duplicatas exatas (opcional)
    if valor not in dados_extraidos[contexto][chave]:
        dados_extraidos[contexto][chave].append(valor)

# --- PROCESSAMENTO ---

contexto_atual = None 

# Simulando um texto onde pode haver múltiplos dados
texto_separado = texto_completo.split('\n')

for linha in texto_separado:
    linha_limpa = linha.strip()
    linha_lower = linha_limpa.lower()
    
    if not linha_limpa:
        continue

    # --- PASSO 1: Identificar Contexto ---
    if any(k in linha_lower for k in palavras_secao["prestador"]):
        contexto_atual = "prestador"
        continue
        
    elif any(k in linha_lower for k in palavras_secao["tomador"]):
        contexto_atual = "tomador"
        continue

    if contexto_atual is None:
        continue

    # --- PASSO 2: Extração Genérica (Regex) ---
    # Iteramos sobre todos os tipos (cnpj, cpf, email, telefone) automaticamente
    for tipo_dado, lista_regex in padroes.items():
        for regex in lista_regex:
            # re.findall retorna uma LISTA com tudo que achou na linha
            encontrados = re.findall(regex, linha_limpa)
            
            for item in encontrados:
                adicionar_dado(contexto_atual, tipo_dado, item)

    # --- PASSO 3: Extração de Campos de Texto (Razão Social / Endereço) ---
    
    # Razão Social
    for key in palavras_campos["razao_social"]:
        if key in linha_lower:
            # rf"" corrige o Warning de escape sequence
            valor = re.sub(rf"{key}[:\s]*", "", linha_limpa, flags=re.IGNORECASE).strip()
            if valor:
                adicionar_dado(contexto_atual, "razao_social", valor)
            break # Para de procurar outras chaves de nome NESTA linha

    # Endereço
    for key in palavras_campos["endereco"]:
        if key in linha_lower:
            valor = re.sub(rf"{key}[:\s]*", "", linha_limpa, flags=re.IGNORECASE).strip()
            if valor:
                adicionar_dado(contexto_atual, "endereco", valor)
            break

# --- RESULTADOS ---
import json
print(json.dumps(dados_extraidos, indent=4, ensure_ascii=False))
# Exibindo o resultado organizado
# print("--- DADOS DO PRESTADOR ---")
# print(dados_extraidos["prestador"])
# print("\n--- DADOS DO TOMADOR ---")
# print(dados_extraidos["tomador"])

# # Exibindo a imagem com os contornos e retângulos
# cv2.imshow('Imagem com Contornos', imagem)
# cv2.waitKey(0)
# cv2.destroyAllWindows()