import os
import re
import pandas as pd

CAMINHO_FORMULADOS = os.path.join("data", "agrofitprodutosformulados.csv")
CAMINHO_TECNICOS = os.path.join("data", "agrofitprodutostecnicos.csv")

SAIDA_FORMULADOS_LIMPO = os.path.join("data", "formulados_unicos_limpos.csv")
SAIDA_TECNICOS_LIMPO = os.path.join("data", "tecnicos_unicos_limpos.csv")


def carregar_csv_mapa(caminho):
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            return pd.read_csv(caminho, sep=";", encoding=encoding, dtype=str, low_memory=False)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Não foi possível ler o arquivo: {caminho}")


def limpar_nome_empresa(nome):
    """
    Remove a cidade/UF do final do nome da empresa titular (ex: '- Londrina/PR' ou 'São Paulo/SP')
    """
    if not isinstance(nome, str):
        return "NÃO INFORMADO"
    # Remove padrões como '- Cidade/UF' ou 'Cidade/UF' no final
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


def organizar_formulados():
    print("[1/2] Lendo e limpando base de Produtos Formulados...")
    df_bruto = carregar_csv_mapa(CAMINHO_FORMULADOS)
    total_linhas_brutas = len(df_bruto)

    df_bruto.columns = df_bruto.columns.str.strip()
    for col in df_bruto.columns:
        df_bruto[col] = df_bruto[col].fillna("").astype(str).str.strip()

    # Conta quantas combinações de cultura/praga cada NR_REGISTRO possui antes de remover duplicatas
    contagem_usos = df_bruto.groupby("NR_REGISTRO").size().rename("QTD_INDICACOES_CULTURA_PRAGA")

    df_unico = df_bruto.drop_duplicates(subset=["NR_REGISTRO"]).copy()
    df_unico = df_unico.merge(contagem_usos, on="NR_REGISTRO", how="left")

    df_unico["TIPO_DEFENSIVO"] = df_unico.apply(classificar_origem_biologica, axis=1)

    df_unico["PAIS_FABRICANTE_PRINCIPAL"] = (
        df_unico["EMPRESA_PAIS_TIPO"]
        .str.extract(r"<([^>]+)>", expand=False)
        .fillna("NÃO INFORMADO")
        .str.upper()
        .str.strip()
    )

    df_unico["TITULAR_LIMPO"] = df_unico["TITULAR_DE_REGISTRO"].apply(limpar_nome_empresa)

    # Padroniza Ingrediente Ativo em MAIÚSCULAS para juntar 'glifosato' e 'Glifosato'
    df_unico["INGREDIENTE_ATIVO_PRINCIPAL"] = (
        df_unico["INGREDIENTE_ATIVO"]
        .str.split(r"\(").str[0]
        .str.strip()
        .str.upper()
    )

    df_unico.to_csv(SAIDA_FORMULADOS_LIMPO, sep=";", index=False, encoding="utf-8-sig")
    print(f"      -> {total_linhas_brutas} linhas brutas consolidadas em {len(df_unico)} produtos formulados únicos.")
    return df_unico


def organizar_tecnicos():
    print("\n[2/2] Lendo e limpando base de Produtos Técnicos...")
    df_bruto = carregar_csv_mapa(CAMINHO_TECNICOS)

    df_bruto.columns = df_bruto.columns.str.strip()
    for col in df_bruto.columns:
        df_bruto[col] = df_bruto[col].fillna("").astype(str).str.strip()

    df_bruto = df_bruto.rename(columns={
        "NUMERO_REGISTRO": "NR_REGISTRO",
        "PRODUTO_TECNICO_MARCA_COMERCIAL": "MARCA_COMERCIAL",
        "INGREDIENTE_ATIVO(GRUPO_QUIMICI)(CONCENTRACAO)": "INGREDIENTE_ATIVO",
        "TITULAR_REGISTRO": "TITULAR_DE_REGISTRO",
        "EMPRESA_<PAIS>_TIPO": "EMPRESA_PAIS_TIPO",
    })

    df_unico = df_bruto.drop_duplicates(subset=["NR_REGISTRO"]).copy()

    df_unico["PAIS_FABRICANTE_PRINCIPAL"] = (
        df_unico["EMPRESA_PAIS_TIPO"]
        .str.extract(r"<([^>]+)>", expand=False)
        .fillna("NÃO INFORMADO")
        .str.upper()
        .str.strip()
    )

    df_unico["TITULAR_LIMPO"] = df_unico["TITULAR_DE_REGISTRO"].apply(limpar_nome_empresa)

    df_unico["INGREDIENTE_ATIVO_PRINCIPAL"] = (
        df_unico["INGREDIENTE_ATIVO"]
        .str.split(r"\(").str[0]
        .str.strip()
        .str.upper()
    )

    df_unico.to_csv(SAIDA_TECNICOS_LIMPO, sep=";", index=False, encoding="utf-8-sig")
    print(f"      -> {len(df_unico)} produtos técnicos únicos salvos.")
    return df_unico


def main():
    df_formulados = organizar_formulados()
    df_tecnicos = organizar_tecnicos()

    print("\nTop 5 Ingredientes Ativos em Produtos Técnicos (após padronizar maiúsculas):")
    print(df_tecnicos["INGREDIENTE_ATIVO_PRINCIPAL"].value_counts().head(5).to_string())

    print("\nTop 5 Empresas Titulares de Produtos Formulados (após limpar Cidade/UF):")
    print(df_formulados["TITULAR_LIMPO"].value_counts().head(5).to_string())


if __name__ == "__main__":
    main()