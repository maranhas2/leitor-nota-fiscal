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
    print(f"Processando imagem: {img_path}")
    imagem = cv2.imread(img_path)

    if imagem is not None:
        imagem_grande = cv2.resize(imagem, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    else:
        print(f"Erro ao carregar: {img_path}")

    imagem_cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    
    _, imagem_binaria = cv2.threshold(imagem_cinza, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    texto_pagina = pytesseract.image_to_string(imagem_binaria, lang='por+eng', config='--psm 3 --psm 6')
    texto_completo += texto_pagina + "\n"


import re
import json

padroes = {
    "cnpj": [r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"], 
    "cpf": [r"\d{3}\.\d{3}\.\d{3}-\d{2}"],
    "email": [r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"],
    "telefone": [r"\(?\d{2}\)?\s*?\d{4,5}-?\d{4}"],
    "nf-e": [r'\b(?:\d[\s.]*){44}\b'],
    "cep": [r"\d{5}\-\d{3}"]
}

palavras_secao = {
    "prestador": ["prestador", "emitente", "vendedor", "dados do emitente"],
    "tomador": ["tomador", "destinatário", "cliente", "comprador", "dados do destinatário"]
}

palavras_campos = {
    "razao_social": [
        "nome/razão social", "razão social", "nome do prestador", "nome do emitente"
    ],
    "nome_fantasia" : [
        "nome fantasia", "nome"
    ],
    "endereco": [
        "endereço", "logradouro", "localização", "município", "bairro"
    ],
    "inscricao_municipal": [
        "inscrição municipal", "insc. municipal", " im ", "ccm"
    ],
    "inscricao_estadual": [
        "inscrição estadual", "insc. estadual", " ie "
    ],
    "vencimento": [
        "data de vencimento", "data vencimento", "vencimento", "venc.", "vcto", "validade", "válido"
    ],
    "valor_total": [
        "valor total da nota", "valor total", "valor líquido", 
        "valor a pagar", "total nota"
    ],
    "desconto": [
        "desconto", "dsct", "dsc"
    ],
    "iss": [
        "iss", "issqn", "i.s.s"
    ],
    "icms": [
        "icms", "v. icms", "valor do icms"
    ],
    "ipi": [
        "ipi", "v. ipi"
    ],
    "icms-st": [
        "icms st", "subst", "substituição"
    ],
    "csll": [
        "csll", "c.s.l.l"
    ],
    "cofins": [
        "cofins", "pis/paesp", "p.i.s"
    ],
    "irrf": [
        "irrf", "ir", "i.r", "ir retido", "i.r retido", "i.r. retido"
    ],
    "inss": [
        "inss", "previdencia", "i.n.n.s"
    ]
}

impostos = [
    "iss", "icms", "ipi", "icms-st", "csll","cofins","irrf","inss"
]

todas_chaves = []
for lista in palavras_campos.values():
    todas_chaves.extend(lista)
for lista in palavras_secao.values():
    todas_chaves.extend(lista)

todas_chaves.extend(["cnpj", "cpf", "fone", "cep", "insc est", "ie"])


dados_extraidos = {
    "prestador": {},
    "tomador": {}
}

def limpar_prefixo(linha, chave_detectada):
    """
    Remove a chave e o separador do início.
    Usa regex para ser flexível com 'Nome:', 'Nome ', 'Nome-'
    """
    chave_segura = re.escape(chave_detectada)

    pattern = rf"^.*?{chave_segura}[^a-zA-Z0-9]*" 
    
    valor = re.sub(pattern, "", linha, count=1, flags=re.IGNORECASE).strip()
    return valor

def limpar_sufixo(valor):
    """
    Corta o valor caso encontre o início de outro campo (Stop Words).
    Ex: 'João Silva Endereço: Rua X' -> Retorna apenas 'João Silva'
    """
    if not valor: return ""
    

    for stop_word in sorted(todas_chaves, key=len, reverse=True):
       
        if stop_word.lower() in valor.lower():
            
            padrao_stop = re.escape(stop_word)

            valor = re.split(rf"[:\s.-]{padrao_stop}", valor, flags=re.IGNORECASE)[0]
    
    return valor.strip()

def adicionar_dado(contexto, chave, valor):
    valor = valor.strip(" .:-_")
    if not valor: return

    if chave not in dados_extraidos[contexto]:
        dados_extraidos[contexto][chave] = []

    if valor not in dados_extraidos[contexto][chave]:
        dados_extraidos[contexto][chave].append(valor)

def limpar_e_extrair(linha, chave_detectada):
    """
    Remove tudo que vem ANTES da chave detectada na linha.
    Ex: 'Município: SP Endereço: Rua A' -> Detecta 'Endereço' -> Retorna 'Rua A'
    """
    chave_segura = re.escape(chave_detectada)
    pattern = rf"^.*?{chave_segura}[^:]*:?\s*"
    
    valor = re.sub(pattern, "", linha, count=1, flags=re.IGNORECASE).strip()
    return valor

contexto_atual = None 
texto_separado = texto_completo.split('\n')

for linha in texto_separado:
    linha_limpa = linha.strip()
    linha_lower = linha.lower()
    
    if not linha_limpa:
        continue

    if any(k in linha_lower for k in palavras_secao["prestador"]):
        contexto_atual = "prestador"
    elif any(k in linha_lower for k in palavras_secao["tomador"]):
        contexto_atual = "tomador"

    if contexto_atual is None:
        continue


    for tipo_dado, lista_regex in padroes.items():
        for regex in lista_regex:
            encontrados = re.findall(regex, linha_limpa)
            for item in encontrados:
                adicionar_dado(contexto_atual, tipo_dado, item)

    for tipo_dado, lista_palavras in palavras_campos.items():
        match_encontrado_na_linha = False
        
        for palavra in lista_palavras:
        
            if re.search(rf"\b{re.escape(palavra)}\b", linha_lower):
                valor_temp = limpar_prefixo(linha_limpa, palavra)
                valor_final = limpar_sufixo(valor_temp)
                
                if len(valor_final) > 1:
                    adicionar_dado(contexto_atual, tipo_dado, valor_final)
                    match_encontrado_na_linha = True
                    break
                
print(json.dumps(dados_extraidos, indent=4, ensure_ascii=False))