# Leitor de Nota Fiscal

Sistema de leitura de nota fiscal para testes em python3.12 desenvolvido em um sistema Ubuntu (Linux).

# Environment 

Para iniciar, deve-se criar um environment para utilizar o projeto sem modificar seu sistema linux e instalar os pré-requisitos:

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get install python3.12 python3.12-dev python3.12-venv
sudo apt-get install python3.12 python3-dev python3-venv

# Cria o ambiente virutal
python3.12 -m venv .venv

# Entra no ambiente virtual
source .venv/bin/activate

# Instala as dependências
pip3 install -r requirements.txt
```
# Fora do Environment

Além de configurar o Ambiente, é necessário também instalar o Tesseract fora do venv:

```bash
sudo apt-get install tesseract-ocr
#Caso queira também a versão em português
sudo apt-get install tesseract-ocr-por
```