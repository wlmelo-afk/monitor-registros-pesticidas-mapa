from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup

# Desativa avisos caso o certificado SSL do site .gov.br não seja reconhecido
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Caminhos montados a partir da localização deste arquivo (funciona de qualquer pasta)
RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "data"
ARQUIVO_DATA_COLETA = PASTA_DADOS / "data_coleta.txt"

# Página oficial do conjunto de dados do Agrofit no Portal de Dados Abertos do MAPA
URL_PAGINA_AGROFIT = (
    "https://dados.agricultura.gov.br/dataset/"
    "6c913699-e82e-4da3-a0a1-fb6c431e367f"
)

# Arquivos esperados e seus links diretos (usados se o scraping não os encontrar)
ARQUIVOS_ESPERADOS = {
    "agrofitprodutosformulados.csv": (
        "https://dados.agricultura.gov.br/dataset/6c913699-e82e-4da3-a0a1-fb6c431e367f"
        "/resource/d30b30d7-e256-484e-9ab8-cd40974e1238/download/agrofitprodutosformulados.csv"
    ),
    "agrofitprodutostecnicos.csv": (
        "https://dados.agricultura.gov.br/dataset/6c913699-e82e-4da3-a0a1-fb6c431e367f"
        "/resource/a200c70b-e025-4a9a-be1b-ec7275d7921f/download/agrofitprodutostecnicos.csv"
    ),
}

# Cabeçalho simulando um navegador comum (evita bloqueio 403)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def extrair_links_csv(url_pagina):
    """
    Web Scraping: procura na página do MAPA os links dos dois CSVs do Agrofit.
    Retorna um dicionário {nome_do_arquivo: url}.
    """
    print(f"[1/3] Acessando página do MAPA: {url_pagina}")
    links = {}

    try:
        resposta = requests.get(url_pagina, headers=HEADERS, timeout=30, verify=False)
        resposta.raise_for_status()
        soup = BeautifulSoup(resposta.text, "html.parser")

        for tag_a in soup.find_all("a", href=True):
            href = urljoin(url_pagina, tag_a["href"].strip())
            nome = href.split("/")[-1].split("?")[0].lower()
            if nome in ARQUIVOS_ESPERADOS and nome not in links:
                links[nome] = href

    except requests.RequestException as erro:
        print(f"      [Aviso] Não foi possível varrer a página ({erro}).")

    # Para cada arquivo que não apareceu na página, usa o link direto conhecido
    for nome, link_reserva in ARQUIVOS_ESPERADOS.items():
        if nome in links:
            print(f"      -> {nome}: encontrado via Web Scraping")
        else:
            print(f"      -> {nome}: não encontrado na página, usando link direto")
            links[nome] = link_reserva

    return links


def baixar_arquivo(nome_arquivo, url_arquivo):
    """
    Baixa um arquivo e salva na pasta data/ com o nome esperado.
    """
    caminho = PASTA_DADOS / nome_arquivo
    print(f"[2/3] Baixando {nome_arquivo} (pode levar alguns minutos)...")

    resposta = requests.get(url_arquivo, headers=HEADERS, stream=True, timeout=60, verify=False)
    resposta.raise_for_status()

    with open(caminho, "wb") as arquivo:
        for pedaco in resposta.iter_content(chunk_size=8192):
            if pedaco:
                arquivo.write(pedaco)

    tamanho_mb = caminho.stat().st_size / (1024 * 1024)
    print(f"      -> Salvo em: {caminho} ({tamanho_mb:.2f} MB)")


def main():
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)

    links = extrair_links_csv(URL_PAGINA_AGROFIT)
    for nome, url in links.items():
        baixar_arquivo(nome, url)

    # Registra quando a coleta foi feita (os dados do MAPA mudam com frequência)
    data_coleta = datetime.now().strftime("%d/%m/%Y %H:%M")
    ARQUIVO_DATA_COLETA.write_text(data_coleta, encoding="utf-8")

    print(f"\n[3/3] Coleta finalizada em {data_coleta}. Arquivos em: {PASTA_DADOS}")


if __name__ == "__main__":
    main()