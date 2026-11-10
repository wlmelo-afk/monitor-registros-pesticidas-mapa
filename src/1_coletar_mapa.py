import os
import urllib3
import requests
from bs4 import BeautifulSoup

# Desativa avisos caso o certificado SSL do site .gov.br não seja reconhecido pelo Mac
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Página oficial do conjunto de dados do Agrofit no Portal de Dados Abertos do MAPA
URL_PAGINA_AGROFIT = (
    "https://dados.agricultura.gov.br/dataset/"
    "6c913699-e82e-4da3-a0a1-fb6c431e367f"
)

# Links diretos de segurança (fallback) caso o portal mude o layout do HTML
LINKS_FALLBACK = [
    "https://dados.agricultura.gov.br/dataset/6c913699-e82e-4da3-a0a1-fb6c431e367f/resource/d30b30d7-e256-484e-9ab8-cd40974e1238/download/agrofitprodutosformulados.csv",
    "https://dados.agricultura.gov.br/dataset/6c913699-e82e-4da3-a0a1-fb6c431e367f/resource/a200c70b-e025-4a9a-be1b-ec7275d7921f/download/agrofitprodutostecnicos.csv",
]

# Cabeçalho simulando um navegador comum (evita bloqueio 403)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

PASTA_DADOS = "data"


def extrair_links_csv(url_pagina):
    """
    Faz Web Scraping na página do MAPA para encontrar todos os links de arquivos .csv
    """
    print(f"[1/3] Acessando página do MAPA: {url_pagina}")

    try:
        resposta = requests.get(url_pagina, headers=HEADERS, timeout=30, verify=False)
        resposta.raise_for_status()  # Gera erro se o status HTTP não for 200 (OK)

        # Transforma o texto HTML em uma árvore navegável do BeautifulSoup
        soup = BeautifulSoup(resposta.text, "html.parser")

        links_encontrados = []
        # Procura todas as tags <a href="..."> da página
        for tag_a in soup.find_all("a", href=True):
            href = tag_a["href"].strip()
            if href.lower().endswith(".csv") and href not in links_encontrados:
                links_encontrados.append(href)

        if links_encontrados:
            print(f"      -> {len(links_encontrados)} arquivo(s) CSV encontrado(s) via Web Scraping!")
            return links_encontrados

    except Exception as erro:
        print(f"      [Aviso] Não foi possível varrer o HTML ({erro}). Usando links diretos oficiais.")

    return LINKS_FALLBACK


def baixar_arquivo(url_arquivo, pasta_destino):
    """
    Baixa um arquivo da internet e salva na pasta 'data/'
    """
    os.makedirs(pasta_destino, exist_ok=True)
    nome_arquivo = url_arquivo.split("/")[-1]
    caminho_completo = os.path.join(pasta_destino, nome_arquivo)

    print(f"[2/3] Baixando: {nome_arquivo} ...")
    resposta = requests.get(url_arquivo, headers=HEADERS, stream=True, timeout=60, verify=False)
    resposta.raise_for_status()

    with open(caminho_completo, "wb") as arquivo:
        for pedaco in resposta.iter_content(chunk_size=8192):
            if pedaco:
                arquivo.write(pedaco)

    tamanho_mb = os.path.getsize(caminho_completo) / (1024 * 1024)
    print(f"      -> Salvo em: {caminho_completo} ({tamanho_mb:.2f} MB)")


def main():
    links_csv = extrair_links_csv(URL_PAGINA_AGROFIT)

    for link in links_csv:
        baixar_arquivo(link, PASTA_DADOS)

    print("\n[3/3] Coleta finalizada com sucesso! Confira a pasta 'data/'.")


if __name__ == "__main__":
    main()