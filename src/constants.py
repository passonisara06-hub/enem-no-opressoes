"""
constants.py — Constantes centralizadas do projeto ENEM Nó de Opressões
========================================================================
Orientação teórica: feminismo marxista / Heleieth Saffioti
Conceito central: nó de opressões (raça–gênero–classe como sistema articulado)

NOTA METODOLÓGICA: A partir de 2020, o INEP dividiu os microdados em dois
arquivos (PARTICIPANTES e RESULTADOS) por exigência da LGPD, sem chave de
junção individual. A análise é, portanto, agregada por UF — veja docs/referencias.md.
"""

from pathlib import Path

# ------------------------------------------------------------
# Configuração — mude apenas ANO para outra edição
# ------------------------------------------------------------
ANO = 2025

# Diretórios
DIRETORIO_RAW = Path(f"data/raw")
DIRETORIO_DADOS = Path("data/processed")

# Arquivos de entrada (formato 2025: dois arquivos separados)
ARQUIVO_PARTICIPANTES = DIRETORIO_RAW / f"PARTICIPANTES_{ANO}.csv"
ARQUIVO_RESULTADOS = DIRETORIO_RAW / f"RESULTADOS_{ANO}.csv"

# Arquivos de saída
ARQUIVO_PART_LIMPO = DIRETORIO_DADOS / "participantes_limpo.parquet"
ARQUIVO_RES_LIMPO = DIRETORIO_DADOS / "resultados_limpo.parquet"
ARQUIVO_METRICAS_DEMO = DIRETORIO_DADOS / "metricas_demograficas.parquet"
ARQUIVO_METRICAS_DESEMP = DIRETORIO_DADOS / "metricas_desempenho.parquet"
ARQUIVO_REGRESSAO_ECO = DIRETORIO_DADOS / "regressao_ecologica.parquet"
ARQUIVO_GAPS_REGIONAIS = DIRETORIO_DADOS / "gaps_regionais.parquet"
ARQUIVO_TESTES_KRUSKAL = DIRETORIO_DADOS / "testes_kruskal.parquet"

# ------------------------------------------------------------
# Grupos do nó de opressões
# ------------------------------------------------------------
# Chave composta: "gênero raça_grupo" (string para mapeamento vetorizado)
GRUPOS_NO = {
    "Feminino Negra": "Mulher negra",
    "Feminino Branca": "Mulher branca",
    "Feminino Indígena": "Mulher indígena",
    "Feminino Outras": "Mulher de outra raça",
    "Feminino Não declarado": "Mulher não declarada",
    "Masculino Negra": "Homem negro",
    "Masculino Branca": "Homem branco",
    "Masculino Indígena": "Homem indígena",
    "Masculino Outras": "Homem de outra raça",
    "Masculino Não declarado": "Homem não declarado",
}

# Ordem analítica: do mais ao menos oprimido no nó de opressões
ORDEM_GRUPOS = [
    "Mulher negra",
    "Homem negro",
    "Mulher branca",
    "Homem branco",
    "Mulher indígena",
    "Homem indígena",
    "Mulher de outra raça",
    "Homem de outra raça",
]

GRUPOS_PRINCIPAIS = [
    "Mulher negra",
    "Mulher branca",
    "Homem negro",
    "Homem branco",
]

# ------------------------------------------------------------
# Mapeamentos — Participantes (demografia)
# ------------------------------------------------------------

# Raça/cor conforme categorias IBGE autodeclaradas
MAPA_RACA = {
    0: "Não declarado",
    1: "Branca",
    2: "Preta",
    3: "Parda",
    4: "Amarela",
    5: "Indígena",
}

# Agrupamento analítico: Preta + Parda = Negra
# Justificativa: Saffioti (2004) trata raça como determinação estrutural
MAPA_RACA_GRUPO = {
    "Branca": "Branca",
    "Preta": "Negra",
    "Parda": "Negra",
    "Amarela": "Outras",
    "Indígena": "Indígena",
    "Não declarado": "Não declarado",
}

MAPA_SEXO = {
    "M": "Masculino",
    "F": "Feminino",
}

# Renda familiar mensal — Q007 no formato 2025
# Valores médios (mediana baixa) em R$ por faixa
# Salário mínimo 2025: R$ 1.518,00
MAPA_RENDA_REAIS = {
    "A": 0,        # Nenhuma renda
    "B": 759,      # Até R$ 1.518,00
    "C": 1898,     # R$ 1.518,01 – R$ 2.277,00
    "D": 2657,     # R$ 2.277,01 – R$ 3.036,00
    "E": 3416,     # R$ 3.036,01 – R$ 3.795,00
    "F": 4175,     # R$ 3.795,01 – R$ 4.554,00
    "G": 5313,     # R$ 4.554,01 – R$ 6.072,00
    "H": 6831,     # R$ 6.072,01 – R$ 7.590,00
    "I": 8349,     # R$ 7.590,01 – R$ 9.108,00
    "J": 9867,     # R$ 9.108,01 – R$ 10.626,00
    "K": 11385,    # R$ 10.626,01 – R$ 12.144,00
    "L": 12903,    # R$ 12.144,01 – R$ 13.662,00
    "M": 14421,    # R$ 13.662,01 – R$ 15.180,00
    "N": 16698,    # R$ 15.180,01 – R$ 18.216,00
    "O": 20493,    # R$ 18.216,01 – R$ 22.770,00
    "P": 26565,    # R$ 22.770,01 – R$ 30.360,00
    "Q": 45540,    # Acima de R$ 30.360,00 (mediana alta)
}

# Faixas de renda simplificadas para análise descritiva
BINS_RENDA = [-1, 0, 1518, 4554, 15180, 999999]
LABELS_RENDA = ["Sem renda", "Até 1 SM", "1–3 SM", "3–10 SM", "Mais de 10 SM"]

# Situação de conclusão do ensino médio — formato 2025
MAPA_CONCLUSAO = {
    1: "Já concluíu",
    2: "Concluirá em 2025",
    3: "Concluirá após 2025",
    4: "Não concluíu e não concluirá",
}

# Tipo de ensino — formato 2025
MAPA_ENSINO = {
    1: "Regular",
    2: "Educação Especial",
}

# ------------------------------------------------------------
# Mapeamentos — Resultados (desempenho)
# ------------------------------------------------------------

# Presença — formato 2025 (encoding mudou!)
# 0 = Faltou, 1 = Presente, 2 = Eliminado
MAPA_PRESENCA = {
    0: "Faltou",
    1: "Presente",
    2: "Eliminado",
}

# Dependência administrativa da escola
MAPA_DEPENDENCIA_ADM = {
    1: "Federal",
    2: "Estadual",
    3: "Municipal",
    4: "Privada",
}

# Agrupamento para análise: Pública (Federal+Estadual+Municipal) vs Privada
MAPA_ESCOLA_TIPO = {
    "Federal": "Pública",
    "Estadual": "Pública",
    "Municipal": "Pública",
    "Privada": "Privada",
}

# Notas por área
NOTAS_AREAS = ["NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT"]
NOTAS_TODAS = NOTAS_AREAS + ["NU_NOTA_REDACAO"]

# ------------------------------------------------------------
# Paleta de cores — política e intencional
# Terra para oprimidas/os, azul para privilegiadas/os
# ------------------------------------------------------------
CORES = {
    "Mulher negra": "#8B4513",        # Siena — terra forte
    "Homem negro": "#CD853F",          # Peru — terra clara
    "Mulher branca": "#4682B4",       # Steel blue — aço
    "Homem branco": "#1E3A5F",        # Navy — azul escuro
    "Mulher indígena": "#556B2F",     # Olive — floresta
    "Homem indígena": "#6B8E23",      # Olive drab — mata
    "Mulher de outra raça": "#9370DB", # Medium purple — transição
    "Homem de outra raça": "#7B68EE", # Medium slate blue — transição
    "Pública": "#8B4513",              # Terra — escola pública
    "Privada": "#4682B4",             # Aço — escola privada
}