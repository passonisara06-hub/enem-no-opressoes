"""
grupos.py — Construção de grupos e métricas agregadas
======================================================
Orientação teórica: nó de opressões (Saffioti)

Como os microdados de 2025 estão divididos em PARTICIPANTES e RESULTADOS
sem chave de junção individual (LGPD), as métricas são calculadas
separadamente e depois combinadas no nível agregado por UF.

Uso:
    python src/grupos.py
Saída:
    data/processed/metricas_demograficas.parquet
    data/processed/metricas_desempenho.parquet
"""

import pandas as pd
import numpy as np
from pathlib import Path
from constants import (
    ARQUIVO_PART_LIMPO, ARQUIVO_RES_LIMPO,
    ARQUIVO_METRICAS_DEMO, ARQUIVO_METRICAS_DESEMP,
    GRUPOS_PRINCIPAIS, ORDEM_GRUPOS, NOTAS_TODAS, NOTAS_AREAS,
)


def calcular_metricas_demograficas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula métricas demográficas por UF a partir dos dados de PARTICIPANTES.

    Produz:
    - Proporção de cada grupo do nó por UF
    - Perfil de renda por UF
    - Contagens absolutas
    """
    print("Calculando métricas demográficas...")

    # --- Contagem e proporção por grupo_no por UF ---
    grupo_uf = df.groupby(["uf", "grupo_no"]).size().reset_index(name="n")
    grupo_uf["pct"] = grupo_uf.groupby("uf")["n"].transform(lambda x: x / x.sum() * 100)

    # --- Proporção de grupos principais por UF ---
    principais = grupo_uf[grupo_uf["grupo_no"].isin(GRUPOS_PRINCIPAIS)].copy()
    principais = principais.pivot_table(
        index="uf", columns="grupo_no", values="pct", fill_value=0
    ).reset_index()

    # Renomear colunas para formato longo
    pct_cols = [c for c in principais.columns if c != "uf"]
    principais = principais.melt(
        id_vars="uf", value_vars=pct_cols, var_name="grupo_no", value_name="pct_grupo"
    )

    # --- Perfil de renda por UF ---
    renda_uf = df.groupby(["uf", "faixa_renda"]).size().reset_index(name="n")
    renda_uf["pct_renda"] = renda_uf.groupby("uf")["n"].transform(lambda x: x / x.sum() * 100)
    renda_uf = renda_uf.pivot_table(
        index="uf", columns="faixa_renda", values="pct_renda", fill_value=0
    ).reset_index()

    # --- Renda média por UF ---
    renda_media_uf = df.groupby("uf")["renda_aprox_reais"].mean().reset_index()
    renda_media_uf.columns = ["uf", "renda_media"]

    # --- Contagem total por UF ---
    total_uf = df.groupby("uf").size().reset_index(name="n_total")

    # --- Consolidar métricas demográficas ---
    metricas = principais.merge(total_uf, on="uf", how="left")
    metricas = metricas.merge(renda_media_uf, on="uf", how="left")

    # --- Proporção de pretos/pardos e mulheres por UF ---
    negros_uf = df.groupby("uf").apply(
        lambda g: pd.Series({
            "pct_negra": (g["raca_grupo"] == "Negra").mean() * 100,
            "pct_branca": (g["raca_grupo"] == "Branca").mean() * 100,
            "pct_feminino": (g["genero"] == "Feminino").mean() * 100,
            "pct_mulher_negra": ((g["genero"] == "Feminino") & (g["raca_grupo"] == "Negra")).mean() * 100,
        })
    ).reset_index()
    metricas = metricas.merge(negros_uf, on="uf", how="left")

    # --- Proporção de treineiros por UF ---
    treineiro_uf = df.groupby("uf")["IN_TREINEIRO"].mean().reset_index()
    treineiro_uf.columns = ["uf", "pct_treineiro"]
    treineiro_uf["pct_treineiro"] *= 100
    metricas = metricas.merge(treineiro_uf, on="uf", how="left")

    print(f"  → {len(metricas)} UFs com métricas demográficas")
    print(f"  → {metricas['grupo_no'].nunique()} grupos representados")
    return metricas


def calcular_metricas_desempenho(df: pd.DataFrame) -> dict:
    """
    Calcula métricas de desempenho e presença por UF e tipo de escola
    a partir dos dados de RESULTADOS.

    Produz:
    - Notas médias por UF e tipo de escola
    - Taxas de presença/ausência por UF e tipo de escola
    - Gap público vs privado por UF
    """
    print("Calculando métricas de desempenho...")

    presentes = df[df["presente_ambos_dias"]].copy()

    # --- Notas médias por UF e tipo de escola ---
    agg_dict_notas = {"nota_media": ["size", "mean", "median", "std"]}
    for col in NOTAS_TODAS:
        agg_dict_notas[col] = "mean"

    notas_tipo = presentes.groupby(["uf", "escola_tipo"]).agg(agg_dict_notas).reset_index()
    # Flatten column names
    notas_tipo.columns = [
        "uf" if col[0] == "uf" else
        "escola_tipo" if col[0] == "escola_tipo" else
        f"{col[0]}_{col[1]}" if col[1] else col[0]
        for col in notas_tipo.columns
    ]

    # --- Notas médias por UF (geral) ---
    notas_uf = presentes.groupby("uf").agg(
        n_uf=("nota_media", "size"),
        nota_media_uf=("nota_media", "mean"),
        nota_mediana_uf=("nota_media", "median"),
        **{f"media_uf_{col.lower()}": (col, "mean") for col in NOTAS_TODAS},
    ).reset_index()

    # --- Taxas de presença por UF e tipo de escola ---
    presenca_tipo = df.groupby(["uf", "escola_tipo"]).agg(
        n_total=("presente_ambos_dias", "size"),
        n_presentes=("presente_ambos_dias", "sum"),
    ).reset_index()
    presenca_tipo["pct_presente"] = presenca_tipo["n_presentes"] / presenca_tipo["n_total"] * 100
    presenca_tipo["pct_ausente"] = 100 - presenca_tipo["pct_presente"]

    # --- Taxas de presença por UF (geral) ---
    presenca_uf = df.groupby("uf").agg(
        n_total_uf=("presente_ambos_dias", "size"),
        n_presentes_uf=("presente_ambos_dias", "sum"),
    ).reset_index()
    presenca_uf["pct_presente_uf"] = presenca_uf["n_presentes_uf"] / presenca_uf["n_total_uf"] * 100
    presenca_uf["pct_ausente_uf"] = 100 - presenca_uf["pct_presente_uf"]

    # --- Gap público vs privado por UF ---
    publica = presentes[presentes["escola_tipo"] == "Pública"].groupby("uf")["nota_media"].mean()
    privada = presentes[presentes["escola_tipo"] == "Privada"].groupby("uf")["nota_media"].mean()
    gap_escola = (privada - publica).reset_index()
    gap_escola.columns = ["uf", "gap_publico_privado"]

    # Consolidar tudo em um dict
    metricas = {
        "notas_tipo_escola": notas_tipo,
        "notas_uf": notas_uf,
        "presenca_tipo_escola": presenca_tipo,
        "presenca_uf": presenca_uf,
        "gap_escola": gap_escola,
    }

    for nome, mdf in metricas.items():
        print(f"  → {nome}: {len(mdf)} registros")

    return metricas


def main():
    """Pipeline de grupos: lê parquets limpos e calcula métricas agregadas."""
    # --- Carregar dados ---
    print("Carregando dados limpos...")
    df_part = pd.read_parquet(ARQUIVO_PART_LIMPO)
    df_res = pd.read_parquet(ARQUIVO_RES_LIMPO)

    # --- Métricas demográficas ---
    metricas_demo = calcular_metricas_demograficas(df_part)
    metricas_demo.to_parquet(ARQUIVO_METRICAS_DEMO, index=False)
    print(f"\nMétricas demográficas salvas em: {ARQUIVO_METRICAS_DEMO}")

    # --- Métricas de desempenho ---
    metricas_desemp = calcular_metricas_desempenho(df_res)

    # Salvar cada DataFrame separadamente
    for nome, mdf in metricas_desemp.items():
        caminho = ARQUIVO_METRICAS_DESEMP.parent / f"{nome}.parquet"
        mdf.to_parquet(caminho, index=False)

    # Consolidar métricas de desempenho em um único parquet (notas + presença por UF)
    consolidado = metricas_desemp["notas_uf"].merge(
        metricas_desemp["presenca_uf"], on="uf", how="outer"
    ).merge(
        metricas_desemp["gap_escola"], on="uf", how="outer"
    )
    consolidado.to_parquet(ARQUIVO_METRICAS_DESEMP, index=False)
    print(f"\nMétricas de desempenho consolidadas em: {ARQUIVO_METRICAS_DESEMP}")


if __name__ == "__main__":
    main()