import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# Caminhos montados a partir da localização deste arquivo (funciona de qualquer pasta)
RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "data"
PASTA_OUTPUT = RAIZ / "output"

ENTRADA_FORMULADOS = PASTA_DADOS / "formulados_unicos_limpos.csv"
ENTRADA_TECNICOS = PASTA_DADOS / "tecnicos_unicos_limpos.csv"
ARQUIVO_DATA_COLETA = PASTA_DADOS / "data_coleta.txt"
ARQUIVO_EXCEL_SAIDA = PASTA_OUTPUT / "panorama_registros_pesticidas_mapa.xlsx"

URL_FONTE = "https://dados.agricultura.gov.br/dataset/6c913699-e82e-4da3-a0a1-fb6c431e367f"


def criar_tabela_ranking(df, coluna, nome_coluna_saida, top_n=30):
    """
    Cria um DataFrame de resumo com Quantidade e Participação (%) no mercado
    """
    contagem = df[coluna].replace("", "NÃO INFORMADO").value_counts().head(top_n)
    total = len(df)
    return pd.DataFrame({
        nome_coluna_saida: contagem.index,
        "QTD_REGISTROS": contagem.values,
        "PARTICIPACAO_%": ((contagem.values / total) * 100).round(2),
    })


def criar_aba_sobre(df_form, df_tec):
    """
    Aba de metadados: de onde vieram os dados e quando foram coletados.
    """
    if ARQUIVO_DATA_COLETA.exists():
        data_coleta = ARQUIVO_DATA_COLETA.read_text(encoding="utf-8").strip()
    else:
        data_coleta = "não registrada"

    return pd.DataFrame({
        "ITEM": [
            "Fonte dos dados",
            "Data da coleta",
            "Data de geração do relatório",
            "Produtos formulados únicos",
            "Produtos técnicos únicos",
            "Observação",
        ],
        "INFORMACAO": [
            f"Agrofit / MAPA – Portal de Dados Abertos ({URL_FONTE})",
            data_coleta,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            len(df_form),
            len(df_tec),
            "A base do MAPA é atualizada com frequência; novas coletas podem trazer valores diferentes.",
        ],
    })


def formatar_planilha(caminho_excel):
    """
    Aplica cabeçalho verde-escuro e ajusta a largura das colunas no Excel
    """
    wb = load_workbook(caminho_excel)
    cor_cabecalho = PatternFill(start_color="1F4E3D", end_color="1F4E3D", fill_type="solid")
    fonte_cabecalho = Font(color="FFFFFF", bold=True)

    for ws in wb.worksheets:
        ws.freeze_panes = "A2"  # Congela a primeira linha (cabeçalho)

        for col_idx, col in enumerate(ws.columns, start=1):
            celula_topo = ws.cell(row=1, column=col_idx)
            celula_topo.fill = cor_cabecalho
            celula_topo.font = fonte_cabecalho
            celula_topo.alignment = Alignment(horizontal="center", vertical="center")

            # Largura ideal da coluna (limite de 50 para não ficar gigante)
            maior_texto = max(len(str(celula.value or "")) for celula in col[:200])
            largura = min(max(maior_texto + 4, 14), 50)
            ws.column_dimensions[get_column_letter(col_idx)].width = largura

    wb.save(caminho_excel)


def main():
    for caminho in (ENTRADA_FORMULADOS, ENTRADA_TECNICOS):
        if not caminho.exists():
            sys.exit(
                f"\n[ERRO] Arquivo não encontrado: {caminho}\n"
                f"       Rode antes: python3 src/1_coletar_mapa.py e python3 src/2_organizar_base.py"
            )

    PASTA_OUTPUT.mkdir(parents=True, exist_ok=True)

    print("[1/3] Carregando bases limpas...")
    df_form = pd.read_csv(ENTRADA_FORMULADOS, sep=";", dtype=str).fillna("")
    df_tec = pd.read_csv(ENTRADA_TECNICOS, sep=";", dtype=str).fillna("")

    print("[2/3] Gerando análises de mercado e abas do Excel...")
    abas = {
        "0_Sobre": criar_aba_sobre(df_form, df_tec),
        "1_Quimicos_vs_Biologicos": criar_tabela_ranking(df_form, "TIPO_DEFENSIVO", "CATEGORIA_DEFENSIVO", top_n=10),
        "2_Classes_Agronomicas": criar_tabela_ranking(df_form, "CLASSE", "CLASSE_AGRONOMICA", top_n=20),
        "3_Paises_Prod_Tecnicos": criar_tabela_ranking(df_tec, "PAIS_FABRICANTE_PRINCIPAL", "PAIS_FABRICANTE_PRODUTO_TECNICO", top_n=25),
        "4_Top_Empresas_Formulados": criar_tabela_ranking(df_form, "TITULAR_LIMPO", "EMPRESA_TITULAR_FORMULADOS", top_n=30),
        "5_Top_Empresas_Tecnicos": criar_tabela_ranking(df_tec, "TITULAR_LIMPO", "EMPRESA_TITULAR_TECNICOS", top_n=30),
        "6_Top_Ativos_Tecnicos": criar_tabela_ranking(df_tec, "INGREDIENTE_ATIVO_PRINCIPAL", "INGREDIENTE_ATIVO_TECNICO", top_n=40),
        "7_Top_Ativos_Formulados": criar_tabela_ranking(df_form, "INGREDIENTE_ATIVO_PRINCIPAL", "INGREDIENTE_ATIVO_FORMULADO", top_n=40),
    }

    colunas_form_excel = [
        "NR_REGISTRO", "MARCA_COMERCIAL", "TIPO_DEFENSIVO", "CLASSE",
        "INGREDIENTE_ATIVO_PRINCIPAL", "TITULAR_LIMPO", "PAIS_FABRICANTE_PRINCIPAL",
        "FORMULACAO", "CLASSE_TOXICOLOGICA", "CLASSE_AMBIENTAL", "QTD_INDICACOES_CULTURA_PRAGA",
    ]
    colunas_tec_excel = [
        "NR_REGISTRO", "MARCA_COMERCIAL", "CLASSE", "INGREDIENTE_ATIVO_PRINCIPAL",
        "TITULAR_LIMPO", "PAIS_FABRICANTE_PRINCIPAL", "CLASSIFICACAO_TOXICOLOGICA", "CLASSIFICACAO_AMBIENTAL",
    ]
    abas["8_Base_Formulados_Unicos"] = df_form[colunas_form_excel]
    abas["9_Base_Tecnicos_Unicos"] = df_tec[colunas_tec_excel]

    with pd.ExcelWriter(ARQUIVO_EXCEL_SAIDA, engine="openpyxl") as writer:
        for nome_aba, tabela in abas.items():
            tabela.to_excel(writer, sheet_name=nome_aba, index=False)

    print("[3/3] Aplicando formatação visual na planilha...")
    formatar_planilha(ARQUIVO_EXCEL_SAIDA)
    print(f"\nRelatório Excel gerado com sucesso em: {ARQUIVO_EXCEL_SAIDA}")


if __name__ == "__main__":
    main()