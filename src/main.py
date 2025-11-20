import json
from tools import check_caminho, leitor_texto, todas_chaves, extract_texto

arquivo_default = 'imagens/NFSe_ficticia_layout_completo.pdf'

print("(Caso queira testar com arquivo genérico, aperte ENTER) \nInsira aqui o caminho para o seu arquivo:")
caminho = str(input())

if caminho == "":
    caminho = arquivo_default

caminhos = check_caminho(caminho)

texto_completo = leitor_texto(caminhos)

lista_chaves = todas_chaves()

dados_extraidos = {}

dados_extraidos = extract_texto(
    texto_bruto=texto_completo, 
    dados=dados_extraidos, 
    chaves=lista_chaves
)

print(json.dumps(dados_extraidos, indent=4, ensure_ascii=False))