import pytesseract
import cv2
import os
import re
import json
from pdf2image import convert_from_path

pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  

caminho = 'imagens/NFSe_ficticia_layout_completo.pdf'

def check_caminho(caminho):
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
    else:
        if os.path.isfile(caminho):
            return print("O arquivo não é PNG, JPG ou PDF.")
        else:
            return print(f"Erro: O arquivo '{caminho}' não foi encontrado.")
    try:
        os.path.isfile(caminho)
    except Exception as e:
        return print(f"O arquivo '{caminho}' não foi encontrado. Erro: {e}")
    return caminhos

def leitor_texto(caminhos):
    texto_completo = ""
    for caminho_img in caminhos:
        try:
            img = cv2.imread(caminho_img)
        except Exception as e:
            print(f"Erro ao carrgar imagem {caminho_img}: {e}")
        try:
            # img_grande = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            imagem_cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, imagem_binaria = cv2.threshold(imagem_cinza, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            texto_pagina = pytesseract.image_to_string(imagem_binaria, lang='por+eng', config='--psm 3 --psm 6')
            texto_completo += texto_pagina + "\n" 
        except Exception as e:
            print(f"Erro ao processar imagem {caminho_img}: {e}")
    return texto_completo

def reparar_texto_quebrado(texto):
    """
    Função essencial para corrigir quebras de linha erradas do OCR.
    Une linhas que parecem ser continuações lógicas, mas respeita cabeçalhos de seção.
    """
    texto = texto.replace('\x0c', '')
    texto = re.sub(r'\s*:\s*', ': ', texto)
    texto = re.sub(r':\s*\n\s*', ': ', texto)
    texto = re.sub(r'[ \t]+', ' ', texto)

    linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]
    
    return '\n'.join(linhas)


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
    "nome": [
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

campos_impostos = [
    "iss", "icms", "ipi", "icms-st", "csll","cofins","irrf","inss"
]

campos_outros = [
    "vencimento", "valor_total", "desconto", "nf-e"
]

def todas_chaves(campos= palavras_campos, secao= palavras_secao):
    todas_chaves = []
    for lista in campos.values():
        todas_chaves.extend(lista)
    for lista in secao.values():
        todas_chaves.extend(lista)
    todas_chaves.extend(["detalhamento de valores","cnpj", "cpf", "fone", "cep", "insc est", "ie"])
    return todas_chaves


def limpar_prefixo(linha, chave_detectada):
    chave_segura = re.escape(chave_detectada)
    pattern = rf"^.*?{chave_segura}[^a-zA-Z0-9]*" 
    valor = re.sub(pattern, "", linha, count=1, flags=re.IGNORECASE).strip()
    return valor

def limpar_sufixo(valor, chaves):
    if not valor: return ""
    for stop_word in sorted(chaves, key=len, reverse=True):
        if stop_word.lower() in valor.lower():
            padrao_stop = re.escape(stop_word)
            valor = re.split(rf"[:\s.-]{padrao_stop}", valor, flags=re.IGNORECASE)[0]
    return valor.strip()

def adicionar_dado(contexto, chave, valor, dados, impostos, outros):
    valor = valor.strip(" :-_=()><+")
    if not valor: return

    if chave == "telefone":
        apenas_numeros = re.sub(r"\D", "", valor)
        
        if len(apenas_numeros) == 10:
            valor = f"({apenas_numeros[:2]}) {apenas_numeros[2:6]}-{apenas_numeros[6:]}"
        elif len(apenas_numeros) == 11:
            valor = f"({apenas_numeros[:2]}) {apenas_numeros[2:7]}-{apenas_numeros[7:]}"
        elif len(apenas_numeros) > 0:
             valor = apenas_numeros 

    if chave == "vencimento" and not re.search(r'\d', valor):
        return 

    chave_final = chave 
    if chave in impostos or chave in outros:
        chave_final = chave
    elif contexto:
        chave_final = f"{chave}_{contexto}"
    else:
        chave_final = chave

    if chave_final not in dados:
        dados[chave_final] = []

    if valor not in dados[chave_final]:
        dados[chave_final].append(valor)

def extract_texto(texto_bruto, dados, chaves, padroes=padroes, secao=palavras_secao, campos=palavras_campos, impostos=campos_impostos, outros=campos_outros):
    linhas = reparar_texto_quebrado(texto_bruto).split('\n')
    contexto_atual = "prestador" 

    for linha in linhas:
        linha_limpa = linha.strip()
        linha_lower = linha.lower()
        
        if not linha_limpa:
            continue

        # Detecta mudança de contexto
        if any(k in linha_lower for k in secao["prestador"]):
            contexto_atual = "prestador"
        elif any(k in linha_lower for k in secao["tomador"]):
            contexto_atual = "tomador"

        dados_encontrados_na_linha = []

        for tipo_dado, lista_palavras in campos.items():
            for palavra in lista_palavras:
                if re.search(rf"\b{re.escape(palavra)}\b", linha_lower):
                    valor_temp = limpar_prefixo(linha_limpa, palavra)
                    valor_final = limpar_sufixo(valor_temp, chaves)
                    
                    if tipo_dado == "email" and " " in valor_final:
                        valor_final = valor_final.split(" ")[0]
                    
                    if len(valor_final) > 1:
                        adicionar_dado(contexto_atual, tipo_dado, valor_final, 
                                     dados=dados, impostos=impostos, outros=outros)
                        dados_encontrados_na_linha.append(tipo_dado)
                        break 

        for tipo_dado, lista_regex in padroes.items():
            if tipo_dado in dados_encontrados_na_linha:
                continue
                
            for regex in lista_regex:
                encontrados = re.findall(regex, linha_limpa)
                for item in encontrados:
                    adicionar_dado(contexto_atual, tipo_dado, item, 
                                 dados=dados, impostos=impostos, outros=outros)

    return dados

if __name__ == "__main__":
    caminho_arquivo = 'imagens/NFSe_ficticia_layout_3_paginas1.jpg'

    print(f"--- Iniciando processamento de: {caminho_arquivo} ---")

    lista_imagens = check_caminho(caminho_arquivo)

    if lista_imagens:
        texto_extraido = leitor_texto(lista_imagens)

        dados_dict = {}
        lista_chaves_bloqueio = todas_chaves()

        resultado = extract_texto(texto_extraido, dados_dict, lista_chaves_bloqueio)

        print("\n--- JSON Resultado ---")
        print(json.dumps(resultado, indent=4, ensure_ascii=False))
    else:
        print("Não foi possível processar o arquivo.")