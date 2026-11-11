# Monitor de Registros de Defensivos Agrícolas (MAPA / Agrofit)

Automação em **Python** que coleta as bases públicas de defensivos agrícolas registrados no Brasil (**Agrofit / Ministério da Agricultura e Pecuária**), organiza os dados e gera um relatório em **Excel** pronto para análise.

> **Relatório gerado:** [`output/panorama_registros_pesticidas_mapa.xlsx`](output/panorama_registros_pesticidas_mapa.xlsx)

---

## Principais resultados

> Números referentes à coleta de **10/11/2026**. O MAPA atualiza a base com frequência, então uma nova execução pode trazer valores diferentes. A data exata da coleta fica registrada na aba `0_Sobre` da planilha.

| Indicador | Resultado |
|---|---|
| **Produtos formulados únicos** | **4.432** *(consolidados a partir de 281.823 linhas brutas de indicações cultura × praga)* |
| **Produtos técnicos únicos** | **3.024** |
| **Origem (formulados)** | **3.509 químicos/sintéticos** (79,2%) vs. **923 biológicos/bioinsumos** (20,8%) |
| **Países fabricantes (produtos técnicos)** | 1º **China** (2.071 / 68,5%) · 2º **Índia** (258 / 8,5%) · 3º **Brasil** (84) · 4º **EUA** (72) |
| **Top 5 ingredientes ativos (produtos técnicos)** | **Protioconazol** (93) · **Azoxistrobina** (72) · **Glifosato** (71) · **Tebuconazol** (68) · **Glufosinato - sal de amônio** (58) |
| **Top 5 titulares (formulados)** | **Syngenta** (269) · **Nortox** (172) · **Adama** (163) · **UPL** (162) · **Rainbow** (159) |

---

## Tratamento da base

1. **Desduplicação por registro (`NR_REGISTRO`):** a base bruta repete o mesmo produto para cada combinação de cultura e praga. O pipeline conta essas indicações (`QTD_INDICACOES_CULTURA_PRAGA`) e consolida um registro por produto.
2. **País do fabricante via regex:** extrai o país embutido em textos como `(Empresa<ÍNDIA>FABRICANTE)`.
3. **Padronização de titulares:** remove sufixos de município/UF (ex.: `- Londrina/PR`) que fragmentariam a contagem por empresa.
4. **Padronização de ingredientes ativos:** unifica maiúsculas/minúsculas (`glifosato` × `Glifosato`), separa o ativo da concentração e corrige erros de grafia nos cabeçalhos originais (`GRUPO_QUIMICI`).
5. **Validação de layout:** se o MAPA alterar o nome de alguma coluna, o script para com uma mensagem indicando o que mudou.

---

## Estrutura do projeto

```text
monitor-registros-pesticidas-mapa/
├── src/
│   ├── 1_coletar_mapa.py     # Web Scraping (requests + BeautifulSoup) no Portal de Dados Abertos do MAPA
│   ├── 2_organizar_base.py   # Limpeza, padronização e classificação agronômica (pandas)
│   └── 3_gerar_excel.py      # Relatório em Excel com 10 abas formatadas (openpyxl)
├── data/                     # CSVs brutos e tratados (gerados localmente, fora do Git)
├── output/
│   └── panorama_registros_pesticidas_mapa.xlsx
├── requirements.txt
└── README.md
```

---

## Como executar

**Requisitos:** Python 3 (testado com Python 3.6.9) e cerca de 500 MB livres (o arquivo bruto do MAPA tem aproximadamente 380 MB). Os scripts podem ser executados a partir de qualquer pasta.

### macOS / Linux

```bash
git clone https://github.com/wlmelo-afk/monitor-registros-pesticidas-mapa.git
cd monitor-registros-pesticidas-mapa
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 src/1_coletar_mapa.py
python3 src/2_organizar_base.py
python3 src/3_gerar_excel.py
```

### Windows (PowerShell)

```powershell
git clone https://github.com/wlmelo-afk/monitor-registros-pesticidas-mapa.git
cd monitor-registros-pesticidas-mapa
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python src\1_coletar_mapa.py
python src\2_organizar_base.py
python src\3_gerar_excel.py
```

> Se o PowerShell bloquear a ativação do ambiente virtual, rode uma vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

O download da etapa 1 pode levar alguns minutos, dependendo da conexão.

---

## Fonte dos dados

[Agrofit – Portal de Dados Abertos do MAPA](https://dados.agricultura.gov.br/dataset/6c913699-e82e-4da3-a0a1-fb6c431e367f)