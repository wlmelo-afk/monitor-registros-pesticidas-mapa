import os
import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ENTRADA_FORMULADOS = os.path.join("data", "formulados_unicos_limpos.csv")
ENTRADA_TECNICOS = os.path.join("data", "tecnicos_unicos_limpos.csv")
ARQUIVO_EXCEL_SAIDA = os.path.join("output", "panorama_registros_pesticidas_mapa.xlsx")


def criar_tabela_ranking(df, coluna, nome_coluna_saida, top_n=30):
    """
    Cria um DataFrame de resumo com Quantidade e Participação (%) no mercado
    """
    contagem = df[coluna].replace("", "NÃO INFORMADO").value_counts().head(top_n)
    total = len(df)
    resumo = pd.DataFrame({
        nome_coluna_saida: contagem.index,
        "QTD_REGISTROS": contagem.values,
        "PARTICIPACAO_%": ((contagem.values / total) * 100).round(2)
    })
    return resumo


def formatar_planilha(caminho_excel):
    """
    Aplica cabeçalho verde-escuro (estilo agronegócio) e ajusta a largura das colunas no Excel
    """
    from openpyxl import load_workbook

    wb = load_workbook(caminho_excel)
    cor_cabecalho = PatternFill(start_color="1F4E3D", end_color="1F4E3D", fill_type="solid")
    fonte_cabecalho = Font(color="FFFFFF", bold=True)

    for ws in wb.worksheets:
        ws.freeze_panes = "A2"  # Congela a primeira linha (cabeçalho) para facilitar rolagem

        for col_idx, col in enumerate(ws.columns, start=1):
            # Formata a célula do cabeçalho (linha 1)
            celula_topo = ws.cell(row=1, column=col_idx)
            celula_topo.fill = cor_cabecalho
            celula_topo.font = fonte_cabecalho
            celula_topo.alignment = Alignment(horizontal="center", vertical="center")

            # Calcula a largura ideal da coluna (com limite máximo de 50 para não ficar gigante)
            maior_texto = max(len(str(celula.value or "")) for celula in col[:200])
            largura = min(max(maior_texto + 4, 14), 50)
            ws.column_dimensions[get_column_letter(col_idx)].width = largura

    wb.save(caminho_excel)


def main():
    os.makedirs("output", exist_ok=True)

    print("[1/3] Carregando bases limpas...")
    df_form = pd.read_csv(ENTRADA_FORMULADOS, sep=";", dtype=str).fillna("")
    df_tec = pd.read_csv(ENTRADA_TECNICOS, sep=";", dtype=str).fillna("")

    print("[2/3] Gerando análises de mercado e abas do Excel...")
    # 1. Resumo Químicos vs. Biológicos e Classes Agronômicas
    aba_resumo_tipo = criar_tabela_ranking(df_form, "TIPO_DEFENSIVO", "CATEGORIA_DEFENSIVO", top_n=10)
    aba_resumo_classe = criar_tabela_ranking(df_form, "CLASSE", "CLASSE_AGRONOMICA", top_n=20)

    # 2. Países de origem dos Produtos Técnicos (China, Índia, Brasil...)
    aba_paises_tec = criar_tabela_ranking(df_tec, "PAIS_FABRICANTE_PRINCIPAL", "PAIS_FABRICANTE_PRODUTO_TECNICO", top_n=25)

    # 3. Top Empresas Titulares (Formulados e Técnicos)
    aba_titulares_form = criar_tabela_ranking(df_form, "TITULAR_LIMPO", "EMPRESA_TITULAR_FORMULADOS", top_n=30)
    aba_titulares_tec = criar_tabela_ranking(df_tec, "TITULAR_LIMPO", "EMPRESA_TITULAR_TECNICOS", top_n=30)

    # 4. Top Ingredientes Ativos (Concorrência em Produtos Técnicos e Formulados)
    aba_ativos_tec = criar_tabela_ranking(df_tec, "INGREDIENTE_ATIVO_PRINCIPAL", "INGREDIENTE_ATIVO_TECNICO", top_n=40)
    aba_ativos_form = criar_tabela_ranking(df_form, "INGREDIENTE_ATIVO_PRINCIPAL", "INGREDIENTE_ATIVO_FORMULADO", top_n=40)

    # Colunas principais para as bases completas ficarem limpas e fáceis de filtrar no Excel
    colunas_form_excel = [
        "NR_REGISTRO", "MARCA_COMERCIAL", "TIPO_DEFENSIVO", "CLASSE",
        "INGREDIENTE_ATIVO_PRINCIPAL", "TITULAR_LIMPO", "PAIS_FABRICANTE_PRINCIPAL",
        "FORMULACAO", "CLASSE_TOXICOLOGICA", "CLASSE_AMBIENTAL", "QTD_INDICACOES_CULTURA_PRAGA"
    ]
    colunas_tec_excel = [
        "NR_REGISTRO", "MARCA_COMERCIAL", "CLASSE", "INGREDIENTE_ATIVO_PRINCIPAL",
        "TITULAR_LIMPO", "PAIS_FABRICANTE_PRINCIPAL", "CLASSIFICACAO_TOXICOLOGICA", "CLASSIFICACAO_AMBIENTAL"
    ]

    with pd.ExcelWriter(ARQUIVO_EXCEL_SAIDA, engine="openpyxl") as writer:
        aba_resumo_tipo.to_excel(writer, sheet_name="1_Quimicos_vs_Biologicos", index=False)
        aba_resumo_classe.to_excel(writer, sheet_name="2_Classes_Agronomicas", index=False)
        aba_paises_tec.to_excel(writer, sheet_name="3_Paises_Prod_Tecnicos", index=False)
        aba_titulares_form.to_excel(writer, sheet_name="4_Top_Empresas_Formulados", index=False)
        aba_titulares_tec.to_excel(writer, sheet_name="5_Top_Empresas_Tecnicos", index=False)
        aba_ativos_tec.to_excel(writer, sheet_name="6_Top_Ativos_Tecnicos", index=False)
        aba_ativos_form.to_excel(writer, sheet_name="7_Top_Ativos_Formulados", index=False)
        df_form[colunas_form_excel].to_excel(writer, sheet_name="8_Base_Formulados_Unicos", index=False)
        df_tec[colunas_tec_excel].to_excel(writer, sheet_name="9_Base_Tecnicos_Unicos", index=False)

    print("[3/3] Aplicando formatação visual na planilha...")
    formatar_planilha(ARQUIVO_EXCEL_SAIDA)
    print(f"\nRelatório Excel gerado com sucesso em: {ARQUIVO_EXCEL_SAIDA}")


if __name__ == "__main__":
    main()