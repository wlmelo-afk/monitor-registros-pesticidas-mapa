# Monitor e Consolidador de Registros de Defensivos Agrícolas (MAPA / Agrofit)

Automação em **Python** para coleta via *Web Scraping*, higienização de bases públicas e geração de relatórios executivos em **Excel** sobre os registros de defensivos agrícolas (químicos e biológicos) aprovados no Brasil pelo **Ministério da Agricultura e Pecuária (MAPA / Agrofit)**.

> **Planilha gerada pelo projeto:** O relatório completo em Excel pode ser baixado diretamente em [`output/panorama_registros_pesticidas_mapa.xlsx`](output/panorama_registros_pesticidas_mapa.xlsx).

---

## Principais Insights Extraídos pela Automação

A partir do processamento automatizado das bases oficiais de **Produtos Formulados** e **Produtos Técnicos** do Agrofit/MAPA, o pipeline identificou:

| Indicador | Resultado Consolidado |
|---|---|
| **Produtos Formulados Únicos Registrados** | **4.432 registros** *(consolidados a partir de 281.823 linhas brutas de indicações cultura × praga)* |
| **Produtos Técnicos Únicos Registrados** | **3.024 registros** |
| **Divisão por Origem (Formulados)** | **3.509 Químicos/Sintéticos** (79,2%) vs. **923 Biológicos/Bioinsumos** (20,8%) |
| **Top Países Fabricantes (Produtos Técnicos)** | 1º **China** (2.071 registros / 68,5%) · 2º **Índia** (258 / 8,5%) · 3º **Brasil** (84) · 4º **EUA** (72) |
| **Top 5 Moléculas em Produtos Técnicos** | 1º **Protioconazol** (93) · 2º **Azoxistrobina** (72) · 3º **Glifosato** (71) · 4º **Tebuconazol** (68) · 5º **Glufosinato - sal de amônio** (58) |
| **Top 5 Titulares (Produtos Formulados)** | 1º **Syngenta** (269) · 2º **Nortox** (172) · 3º **Adama** (163) · 4º **UPL** (162) · 5º **Rainbow** (159) |

---

## Tratamento e Organização da Base (Data Cleaning)

Bases públicas governamentais apresentam inconsistências estruturais que distorcem análises diretas no Excel. Este pipeline corrige automaticamente:

1. **Desduplicação por Registro (`NR_REGISTRO`):** A base bruta de produtos formulados possui **281.823 linhas**, pois repete o mesmo produto para cada combinação de cultura e alvo biológico. O script contabiliza a abrangência de usos (`QTD_INDICACOES_CULTURA_PRAGA`) e consolida os **4.432 produtos únicos**.
2. **Extração de País do Fabricante via Regex:** Extrai o país de origem embutido em strings compostas na coluna `EMPRESA_PAIS_TIPO` (ex.: `<CHINA, REPUBLICA POPULAR>`, `<ÍNDIA>`).
3. **Padronização de Empresas Titulares:** Remove sufixos despadronizados de município/UF (como `- Londrina/PR` ou `São Paulo/SP`) para evitar fragmentação na contagem por empresa.
4. **Padronização de Ingredientes Ativos e Colunas:** Corrige divergências de caixa alta/baixa (ex.: `glifosato` vs. `Glifosato`), isola o ingrediente ativo principal da concentração e corrige erros de grafia nos cabeçalhos originais (`GRUPO_QUIMICI`).

---

## Estrutura do Projeto

```text
monitor-registros-pesticidas-mapa/
├── src/
│   ├── 1_coletar_mapa.py     # Web Scraping (requests + BeautifulSoup) no Portal de Dados Abertos do MAPA
│   ├── 2_organizar_base.py   # Limpeza, padronização e classificação agronômica (pandas)
│   └── 3_gerar_excel.py      # Geração de relatório em Excel com 9 abas formatadas (openpyxl)
├── data/                     # Armazenamento local dos CSVs brutos e tratados
├── output/
│   └── panorama_registros_pesticidas_mapa.xlsx
├── requirements.txt
└── README.md
```

---

## Como Executar

```bash
# 1. Instale as dependências
pip install -r requirements.txt

# 2. Execute as 3 etapas do pipeline
python3 src/1_coletar_mapa.py
python3 src/2_organizar_base.py
python3 src/3_gerar_excel.py
```