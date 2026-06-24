"""
ingestao.py — Leitura e limpeza dos microdados do ENEM 2025
=============================================================
Orientação teórica: feminismo marxista / Heleieth Saffioti
Conceito central: nó de opressões (raça–gênero–classe como sistema articulado)

NOTA METODOLÓGICA: A partir de 2020, o INEP dividiu os microdados em dois
arquivos (PARTICIPANTES e RESULTADOS) por exigência da LGPD, sem chave de
junção individual. A análise é agregada por UF.

Uso:
    python src/ingestao.py
Saída:
    data/processed/participantes_limpo.parquet
    data/processed/resultados_limpo.parquet
"""

import pandas as pd
import numpy as np
from pathlib import Path
from constants import (
    ANO, ARQUIVO_PARTICIPANTES, ARQUIVO_RESULTADOS,
    ARQUIVO_PART_LIMPO, ARQUIVO_RES_LIMPO,
    MAPA_RACA, MAPA_RACA_GRUPO, MAPA_SEXO, MAPA_RENDA_REAIS,
    MAPA_CONCLUSAO, MAPA_ENSINO, MAPA_DEPENDENCIA_ADM, MAPA_ESCOLA_TIPO,
    BINS_RENDA, LABELS_RENDA, NOTAS_TODAS, GRUPOS_NO,
)

# ------------------------------------------------------------
# Colunas a carregar de cada arquivo (economia de memória)
# ------------------------------------------------------------

COLUNAS_PARTICIPANTES = [
    # Identificação estrutural
    "TP_SEXO",              # M / F
    "TP_COR_RACA",          # 0=Não declarado, 1=Branca, 2=Preta,
                            # 3=Parda, 4=Amarela, 5=Indígena
    # Dimensão de classe (proxy)
    "Q007",                  # Renda familiar mensal (A–Q, formato 2025)
    # Contexto geográfico
    "SG_UF_PROVA",
    "NO_MUNICIPIO_PROVA",
    # Características adicionais
    "TP_FAIXA_ETARIA",
    "TP_ST_CONCLUSAO",       # Situação de conclusão do EM
    "TP_ENSINO",             # Tipo de ensino
    "IN_TREINEIRO",          # Treineiro
]

COLUNAS_RESULTADOS = [
    # Presença — encoding 2025: 0=Faltou, 1=Presente, 2=Eliminado
    "TP_PRESENCA_CN",
    "TP_PRESENCA_CH",
    "TP_PRESENCA_LC",
    "TP_PRESENCA_MT",
    # Notas por área
    "NU_NOTA_CN",
    "NU_NOTA_CH",
    "NU_NOTA_LC",
    "NU_NOTA_MT",
    "NU_NOTA_REDACAO",
    # Notas por competência da redação
    "NU_NOTA_COMP1",
    "NU_NOTA_COMP2",
    "NU_NOTA_COMP3",
    "NU_NOTA_COMP4",
    "NU_NOTA_COMP5",
    # Tipo de escola (apenas em RESULTADOS)
    "TP_DEPENDENCIA_ADM_ESC",
    # Contexto geográfico
    "SG_UF_PROVA",
    "NO_MUNICIPIO_PROVA",
]


def ler_participantes(caminho: Path) -> pd.DataFrame:
    """
    Lê o CSV de PARTICIPANTES com encoding e separador corretos.
    Carrega apenas as colunas necessárias para a análise demográfica.
    """
    print(f"Lendo PARTICIPANTES ({caminho})...")
    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="ISO-8859-1",
        usecols=COLUNAS_PARTICIPANTES,
        dtype={"TP_SEXO": str, "Q007": str, "SG_UF_PROVA": str, "NO_MUNICIPIO_PROVA": str},
        low_memory=False,
    )
    print(f"  → {len(df):,} participantes carregados, {df.shape[1]} variáveis")
    return df


def ler_resultados(caminho: Path) -> pd.DataFrame:
    """
    Lê o CSV de RESULTADOS com encoding e separador corretos.
    Carrega apenas as colunas necessárias para análise de desempenho.
    """
    print(f"Lendo RESULTADOS ({caminho})...")
    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="ISO-8859-1",
        usecols=COLUNAS_RESULTADOS,
        dtype={"SG_UF_PROVA": str, "NO_MUNICIPIO_PROVA": str},
        low_memory=False,
    )
    print(f"  → {len(df):,} registros carregados, {df.shape[1]} variáveis")
    return df


def limpar_participantes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica mapeamentos e cria variáveis auxiliares nos dados de PARTICIPANTES.
    """
    df = df.copy()

    # --- Raça/cor ---
    df["raca_label"] = df["TP_COR_RACA"].map(MAPA_RACA).fillna("Não declarado")
    df["raca_grupo"] = df["raca_label"].map(MAPA_RACA_GRUPO).fillna("Não declarado")

    # --- Gênero ---
    df["genero"] = df["TP_SEXO"].map(MAPA_SEXO).fillna("Não informado")

    # --- Nó de opressões: grupo estrutural raça×gênero ---
    # Construção vetorizada com chave composta "gênero raça_grupo"
    df["chave_no"] = df["genero"] + " " + df["raca_grupo"]
    df["grupo_no"] = df["chave_no"].map(GRUPOS_NO).fillna(df["chave_no"])
    df = df.drop(columns=["chave_no"])

    # --- Renda / classe (Q007 no formato 2025) ---
    df["renda_aprox_reais"] = df["Q007"].map(MAPA_RENDA_REAIS)
    df["faixa_renda"] = pd.cut(
        df["renda_aprox_reais"],
        bins=BINS_RENDA,
        labels=LABELS_RENDA,
    )

    # --- Situação de conclusão ---
    df["conclusao_em"] = df["TP_ST_CONCLUSAO"].map(MAPA_CONCLUSAO)

    # --- Tipo de ensino ---
    df["ensino_label"] = df["TP_ENSINO"].map(MAPA_ENSINO).fillna("Não informado")

    # --- UF padronizado ---
    df["uf"] = df["SG_UF_PROVA"].str.strip().str.upper()

    # --- Treineiro ---
    df["treineiro"] = df["IN_TREINEIRO"].map({0: "Não", 1: "Sim"})

    # --- Grupo válido (N >= 1000) ---
    contagem = df["grupo_no"].value_counts()
    grupos_pequenos = contagem[contagem < 1000].index
    df["grupo_no_valido"] = df["grupo_no"].where(
        ~df["grupo_no"].isin(grupos_pequenos), "Outros"
    )

    print(f"  → Participantes limpos. Shape: {df.shape}")
    return df


def limpar_resultados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica mapeamentos e cria variáveis auxiliares nos dados de RESULTADOS.
    Encoding de presença mudou em 2025: 0=Faltou, 1=Presente, 2=Eliminado.
    """
    df = df.copy()

    # --- Presença: encoding 2025 ---
    # Presente em ambos os dias = todos os 4 TP_PRESENCA_* == 1
    cols_presenca = ["TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT"]
    df["presente_ambos_dias"] = (df[cols_presenca] == 1).all(axis=1)
    df["ausente_algum_dia"] = ~df["presente_ambos_dias"]

    # Presença por dia
    df["presente_cn"] = df["TP_PRESENCA_CN"] == 1
    df["presente_ch"] = df["TP_PRESENCA_CH"] == 1
    df["presente_lc"] = df["TP_PRESENCA_LC"] == 1
    df["presente_mt"] = df["TP_PRESENCA_MT"] == 1

    # --- Nota média geral (só para presentes em ambos os dias) ---
    notas = NOTAS_TODAS
    df["nota_media"] = df[notas].mean(axis=1)

    # --- Tipo de escola ---
    # TP_DEPENDENCIA_ADM_ESC: 1=Federal, 2=Estadual, 3=Municipal, 4=Privada, NaN=Não respondeu
    df["dep_adm_label"] = df["TP_DEPENDENCIA_ADM_ESC"].map(MAPA_DEPENDENCIA_ADM)
    df["escola_tipo"] = df["dep_adm_label"].map(MAPA_ESCOLA_TIPO).fillna("Não respondeu")

    # --- UF padronizado ---
    df["uf"] = df["SG_UF_PROVA"].str.strip().str.upper()

    print(f"  → Resultados limpos. Shape: {df.shape}")
    return df


def relatorio_qualidade_participantes(df: pd.DataFrame) -> None:
    """Imprime relatório de qualidade dos dados de participantes."""
    print("\n=== Relatório de qualidade — Participantes ===")
    print(f"Total de participantes: {len(df):,}")
    print(f"\nDistribuição por gênero:\n{df['genero'].value_counts()}")
    print(f"\nDistribuição por raça (grupo):\n{df['raca_grupo'].value_counts()}")
    print(f"\nDistribuição por nó de opressões:\n{df['grupo_no'].value_counts()}")
    print(f"\nDistribuição por faixa de renda:\n{df['faixa_renda'].value_counts().sort_index()}")


def relatorio_qualidade_resultados(df: pd.DataFrame) -> None:
    """Imprime relatório de qualidade dos dados de resultados."""
    print("\n=== Relatório de qualidade — Resultados ===")
    print(f"Total de registros: {len(df):,}")
    print(f"Presentes em ambos os dias: {df['presente_ambos_dias'].sum():,} "
          f"({df['presente_ambos_dias'].mean()*100:.1f}%)")
    print(f"\nTipo de escola:\n{df['escola_tipo'].value_counts()}")
    print(f"\nNota média (presentes): "
          f"{df.loc[df['presente_ambos_dias'], 'nota_media'].mean():.1f}")
    # Mapeamento de área para coluna de presença
    mapa_presenca = {
        "NU_NOTA_CN": "presente_cn",
        "NU_NOTA_CH": "presente_ch",
        "NU_NOTA_LC": "presente_lc",
        "NU_NOTA_MT": "presente_mt",
        "NU_NOTA_REDACAO": "presente_lc",  # Redação é no mesmo dia de LC
    }
    for area in NOTAS_TODAS:
        col_presenca = mapa_presenca[area]
        presentes = df.loc[df[col_presenca], area]
        print(f"  {area}: média={presentes.mean():.1f}, std={presentes.std():.1f}")


def main():
    """Pipeline de ingestão: lê, limpa e salva os dois conjuntos de dados."""
    ARQUIVO_PART_LIMPO.parent.mkdir(parents=True, exist_ok=True)

    # --- Participantes ---
    df_part = ler_participantes(ARQUIVO_PARTICIPANTES)
    df_part = limpar_participantes(df_part)
    relatorio_qualidade_participantes(df_part)
    df_part.to_parquet(ARQUIVO_PART_LIMPO, index=False)
    print(f"\nParticipantes salvos em: {ARQUIVO_PART_LIMPO}")

    # --- Resultados ---
    df_res = ler_resultados(ARQUIVO_RESULTADOS)
    df_res = limpar_resultados(df_res)
    relatorio_qualidade_resultados(df_res)
    df_res.to_parquet(ARQUIVO_RES_LIMPO, index=False)
    print(f"\nResultados salvos em: {ARQUIVO_RES_LIMPO}")


if __name__ == "__main__":
    main()