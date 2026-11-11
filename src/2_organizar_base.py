import re
import sys
from pathlib import Path

import pandas as pd

# Caminhos montados a partir da localização deste arquivo (funciona de qualquer pasta)
RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "data"

CAMINHO_FORMULADOS = PASTA_DADOS / "agrofitprodutosformulados.csv"
CAMINHO_TECNICOS = PASTA_DADOS / "agrofitprodutostecnicos.csv"
SAIDA_FORMULADOS_LIMPO = PASTA_DADOS / "formulados_unicos_limpos.csv"
SAIDA_TECNICOS_LIMPO = PASTA_DADOS / "tecnicos_unicos_limpos.csv"

COLUNAS_FORMULADOS = [
    "NR_REGISTRO", "MARCA_COMERCIAL", "FORMULACAO", "INGREDIENTE_ATIVO",
    "TITULAR_DE_REGISTRO", "CLASSE", "EMPRESA_PAIS_TIPO",
    "CLASSE_TOXICOLOGICA", "CLASSE_AMBIENTAL", "ORGANICOS",
]
COLUNAS_TECNICOS = [  # nomes já padronizados (após o rename)
    "NR_REGISTRO", "MARCA_COMERCIAL", "INGREDIENTE_ATIVO", "CLASSE",
    "TITULAR_DE_REGISTRO", "EMPRESA_PAIS_TIPO",
    "CLASSIFICACAO_TOXICOLOGICA", "CLASSIFICACAO_AMBIENTAL",
]


def carregar_csv_mapa(caminho):
    """
    Lê o CSV do MAPA testando UTF-8 e Latin-1 (comum em bases do governo).
    """
    if not caminho.exists():
        sys.exit(
            f"\n[ERRO] Arquivo não encontrado: {caminho}\n"
            f"       Rode primeiro: python3 src/1_coletar_mapa.py"
        )
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            return pd.read_csv(caminho, sep=";", encoding=encoding, dtype=str, low_memory=False)
        except UnicodeDecodeError:
            continue
    sys.exit(f"\n[ERRO] Não foi possível ler o arquivo: {caminho}")


def validar_colunas(df, colunas_obrigatorias, nome_base):
    """
    Interrompe com uma mensagem clara se o MAPA tiver mudado o layout do arquivo.
    """
    faltando = [c for c in colunas_obrigatorias if c not in df.columns]
    if faltando:
        sys.exit(
            f"\n[ERRO] A base '{nome_base}' não tem as colunas esperadas: {faltando}\n"
            f"       O MAPA pode ter alterado o layout do arquivo.\n"
            f"       Colunas encontradas: {list(df.columns)}"
        )


def limpar_nome_empresa(nome):
    """
    Remove a cidade/UF do final do nome da empresa titular (ex: '- Londrina/PR' ou 'São Paulo/SP')
    """
    if not isinstance(nome, str):
        return "NÃO INFORMADO"
    limpo = re.sub(r"\s*-?\s*[A-Za-zÀ-ÿ\s]+\s*/\s*[A-Z]{2}\s*$", "", nome)
    limpo = limpo.split(" - ")[0].strip()
    return limpo if limpo else nome.strip()


def classificar_origem_biologica(linha):
    texto = f"{linha.get('CLASSE', '')} {linha.get('INGREDIENTE_ATIVO', '')} {linha.get('ORGANICOS', '')}".lower()
    termos_biologicos = [
        "biológico", "biologico", "microbiológico", "microbiologico",
        "agente biológico", "bacillus", "trichoderma", "beauveria",
        "metarhizium", "paecilomyces", "isaria", "cordyceps", "vírus", "virus",
        "extrato", "feromônio", "feromonio", "inimigo natural"
    ]
    for termo in termos_biologicos:
        if termo in texto:
            return "Biológico / Bioinsumo"
    return "Químico / Sintético"


def limpar_textos(df):
    """
    Remove espaços extras dos nomes das colunas e de todos os textos (.strip() = .trim() do Java)
    """
    df.columns = df.columns.str.strip()
    for col in df.columns:
        df[col] = df[col].fillna("").astype(str).str.strip()
    return df


def adicionar_colunas_analiticas(df):
    """
    Cria as colunas padronizadas usadas nos rankings (país, titular e ingrediente ativo).
    """
    df["PAIS_FABRICANTE_PRINCIPAL"] = (
        df["EMPRESA_PAIS_TIPO"]
        .str.extract(r"<([^>]+)>", expand=False)
        .fillna("NÃO INFORMADO")
        .str.upper()
        .str.strip()
    )
    df["TITULAR_LIMPO"] = df["TITULAR_DE_REGISTRO"].apply(limpar_nome_empresa)
    # Padroniza Ingrediente Ativo em MAIÚSCULAS para juntar 'glifosato' e 'Glifosato'
    df["INGREDIENTE_ATIVO_PRINCIPAL"] = (
        df["INGREDIENTE_ATIVO"]
        .str.split(r"\(").str[0]
        .str.strip()
        .str.upper()
    )
    return df


def organizar_formulados():
    print("[1/2] Lendo e limpando base de Produtos Formulados...")
    df_bruto = limpar_textos(carregar_csv_mapa(CAMINHO_FORMULADOS))
    validar_colunas(df_bruto, COLUNAS_FORMULADOS, "Produtos Formulados")
    total_linhas_brutas = len(df_bruto)

    # Conta quantas combinações de cultura/praga cada NR_REGISTRO possui antes de remover duplicatas
    contagem_usos = df_bruto.groupby("NR_REGISTRO").size().rename("QTD_INDICACOES_CULTURA_PRAGA")

    df_unico = df_bruto.drop_duplicates(subset=["NR_REGISTRO"]).copy()
    df_unico = df_unico.merge(contagem_usos, on="NR_REGISTRO", how="left")
    df_unico["TIPO_DEFENSIVO"] = df_unico.apply(classificar_origem_biologica, axis=1)
    df_unico = adicionar_colunas_analiticas(df_unico)

    df_unico.to_csv(SAIDA_FORMULADOS_LIMPO, sep=";", index=False, encoding="utf-8-sig")
    print(f"      -> {total_linhas_brutas} linhas brutas consolidadas em {len(df_unico)} produtos formulados únicos.")
    return df_unico


def organizar_tecnicos():
    print("\n[2/2] Lendo e limpando base de Produtos Técnicos...")
    df_bruto = limpar_textos(carregar_csv_mapa(CAMINHO_TECNICOS))

    # Padroniza os nomes das colunas (inclui o erro de digitação do MAPA: GRUPO_QUIMICI)
    df_bruto = df_bruto.rename(columns={
        "NUMERO_REGISTRO": "NR_REGISTRO",
        "PRODUTO_TECNICO_MARCA_COMERCIAL": "MARCA_COMERCIAL",
        "INGREDIENTE_ATIVO(GRUPO_QUIMICI)(CONCENTRACAO)": "INGREDIENTE_ATIVO",
        "TITULAR_REGISTRO": "TITULAR_DE_REGISTRO",
        "EMPRESA_<PAIS>_TIPO": "EMPRESA_PAIS_TIPO",
    })
    validar_colunas(df_bruto, COLUNAS_TECNICOS, "Produtos Técnicos")

    df_unico = df_bruto.drop_duplicates(subset=["NR_REGISTRO"]).copy()
    df_unico = adicionar_colunas_analiticas(df_unico)

    df_unico.to_csv(SAIDA_TECNICOS_LIMPO, sep=";", index=False, encoding="utf-8-sig")
    print(f"      -> {len(df_unico)} produtos técnicos únicos salvos.")
    return df_unico


def main():
    df_formulados = organizar_formulados()
    df_tecnicos = organizar_tecnicos()

    print("\nTop 5 Ingredientes Ativos em Produtos Técnicos:")
    print(df_tecnicos["INGREDIENTE_ATIVO_PRINCIPAL"].value_counts().head(5).to_string())

    print("\nTop 5 Empresas Titulares de Produtos Formulados:")
    print(df_formulados["TITULAR_LIMPO"].value_counts().head(5).to_string())


if __name__ == "__main__":
    main()