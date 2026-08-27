"""
novas_analises.py — Métricas agregadas por UF: trabalho reprodutivo e capital herdado
=====================================================================================
Orientações teóricas:
- Trabalho reprodutivo (feminismo marxista): carga de cuidado e infraestrutura
  doméstica como determinantes estruturais da participação no ENEM.
- Educação emancipadora: capital cultural e de classe herdado (escolaridade e
  ocupação dos pais) como condição de partida desigual.

Como os microdados de 2025 estão divididos em PARTICIPANTES e RESULTADOS sem
chave de junção individual (LGPD), estas métricas são agregadas por UF e podem
ser correlacionadas ecologicamente com o desempenho (ver inferencial.py).

Uso:
    python src/novas_analises.py
Saída:
    data/processed/trabalho_reprodutivo.parquet
    data/processed/capital_herdado.parquet
"""

import pandas as pd
from pathlib import Path
from constants import (
    ARQUIVO_PART_LIMPO,
    ARQUIVO_TRABALHO_REPRODUTIVO, ARQUIVO_CAPITAL_HERDADO,
    ORDEM_OCUPACAO, ORDEM_ESCOLARIDADE,
)


def _pct_por_uf(df: pd.DataFrame, coluna: str, ordem: "list | None" = None) -> pd.DataFrame:
    """Calcula a proporção (%) de cada categoria de `coluna` por UF.

    Retorna DataFrame longo com colunas: uf, categoria, pct.
    """
    contagem = df.groupby(["uf", coluna]).size().reset_index(name="n")
    contagem["pct"] = contagem.groupby("uf")["n"].transform(lambda x: x / x.sum() * 100)
    contagem = contagem.rename(columns={coluna: "categoria"})

    if ordem:
        # Garantir que "Não informado" (se presente) fique no fim da pilha
        ordem_efetiva = list(ordem)
        for cat in contagem["categoria"].unique():
            if cat not in ordem_efetiva:
                ordem_efetiva.append(cat)
        contagem["categoria"] = pd.Categorical(
            contagem["categoria"], categories=ordem_efetiva, ordered=True
        )
        contagem = contagem.sort_values(["uf", "categoria"])

    return contagem


def calcular_trabalho_reprodutivo(df: pd.DataFrame) -> dict:
    """Métricas de trabalho reprodutivo por UF.

    Produz (DataFrames longos por UF):
    - empregado_domestico: % que contrata empregado doméstico (terceirização do cuidado)
    - maquina_lavar: % com máquina de lavar (infraestrutura que reduz carga doméstica)
    - banheiro: % com banheiro (infraestrutura básica)
    - faixa_pessoas: % por nº de pessoas na residência (carga de cuidado)
    - estado_civil: % por estado civil (responsabilidade familiar)
    - faixa_etaria: % por faixa etária (fase de vida)
    """
    print("Calculando métricas de trabalho reprodutivo...")

    metricas = {
        "empregado_domestico": _pct_por_uf(df, "empregado_domestico"),
        "maquina_lavar": _pct_por_uf(df, "maquina_lavar"),
        "banheiro": _pct_por_uf(df, "banheiro"),
        "faixa_pessoas": _pct_por_uf(df, "faixa_pessoas_residencia"),
        "estado_civil": _pct_por_uf(df, "estado_civil"),
        "faixa_etaria": _pct_por_uf(df, "faixa_etaria_grupo"),
    }

    for nome, mdf in metricas.items():
        print(f"  → {nome}: {len(mdf)} registros")

    return metricas


def calcular_capital_herdado(df: pd.DataFrame) -> dict:
    """Métricas de capital herdado (educação emancipadora) por UF.

    Produz (DataFrames longos por UF):
    - escolaridade_pai: % por escolaridade do pai
    - escolaridade_mae: % por escolaridade da mãe
    - ocupacao_pai: % por ocupação do pai (classe de origem)
    - ocupacao_mae: % por ocupação da mãe (classe de origem)
    - escolaridade_mae_superior: % de mães com ensino superior completo ou pós
    - ocupacao_mae_liberal: % de mães em profissões liberais/direção (Grupo 5)
    """
    print("Calculando métricas de capital herdado...")

    metricas = {
        "escolaridade_pai": _pct_por_uf(df, "escolaridade_pai", ORDEM_ESCOLARIDADE),
        "escolaridade_mae": _pct_por_uf(df, "escolaridade_mae", ORDEM_ESCOLARIDADE),
        "ocupacao_pai": _pct_por_uf(df, "ocupacao_pai", ORDEM_OCUPACAO),
        "ocupacao_mae": _pct_por_uf(df, "ocupacao_mae", ORDEM_OCUPACAO),
    }

    # Indicadores sintéticos por UF (para correlação ecológica)
    # Excluir "Não sei" do denominador — é ausência de informação, não classe de origem
    df_valido_esc = df[df["escolaridade_mae"] != "Não sei"].copy()
    df_valido_ocu_mae = df[df["ocupacao_mae"] != "Não sei"].copy()
    df_valido_ocu_pai = df[df["ocupacao_pai"] != "Não sei"].copy()

    # % de mães com superior completo ou pós-graduação
    sup_mae_uf = df_valido_esc[df_valido_esc["escolaridade_mae"].isin(["Superior completo", "Pós-graduação"])]
    sup_mae_uf = sup_mae_uf.groupby("uf").size().reset_index(name="n_sup_mae")
    total_esc = df_valido_esc.groupby("uf").size().reset_index(name="n_total_esc")
    sintetico = sup_mae_uf.merge(total_esc, on="uf", how="right").fillna(0)
    sintetico["pct_mae_superior"] = sintetico["n_sup_mae"] / sintetico["n_total_esc"] * 100

    # % de mães em profissões liberais/direção (Grupo 5)
    lib_mae = df_valido_ocu_mae[df_valido_ocu_mae["ocupacao_mae"] == "Grupo 5 — Profissional liberal/direção"]
    lib_mae_uf = lib_mae.groupby("uf").size().reset_index(name="n_lib_mae")
    total_ocu_mae = df_valido_ocu_mae.groupby("uf").size().reset_index(name="n_total_ocu_mae")
    sintetico = sintetico.merge(lib_mae_uf, on="uf", how="left").fillna(0)
    sintetico = sintetico.merge(total_ocu_mae, on="uf", how="left")
    sintetico["pct_mae_liberal"] = sintetico["n_lib_mae"] / sintetico["n_total_ocu_mae"] * 100

    # % de pais em trabalho rural/manual (Grupo 1 — mais oprimido)
    rural_pai = df_valido_ocu_pai[df_valido_ocu_pai["ocupacao_pai"] == "Grupo 1 — Trabalho rural/manual"]
    rural_pai_uf = rural_pai.groupby("uf").size().reset_index(name="n_rural_pai")
    total_ocu_pai = df_valido_ocu_pai.groupby("uf").size().reset_index(name="n_total_ocu_pai")
    sintetico = sintetico.merge(rural_pai_uf, on="uf", how="left").fillna(0)
    sintetico = sintetico.merge(total_ocu_pai, on="uf", how="left")
    sintetico["pct_pai_rural"] = sintetico["n_rural_pai"] / sintetico["n_total_ocu_pai"] * 100

    sintetico = sintetico[["uf", "pct_mae_superior", "pct_mae_liberal", "pct_pai_rural"]]
    metricas["sintetico"] = sintetico

    for nome, mdf in metricas.items():
        print(f"  → {nome}: {len(mdf)} registros")

    return metricas


def main():
    """Pipeline: lê participantes limpos e calcula as novas métricas agregadas."""
    print("Carregando dados limpos...")
    df_part = pd.read_parquet(ARQUIVO_PART_LIMPO)

    # --- Trabalho reprodutivo ---
    tr = calcular_trabalho_reprodutivo(df_part)
    for nome, mdf in tr.items():
        caminho = ARQUIVO_TRABALHO_REPRODUTIVO.parent / f"trabalho_reprodutivo_{nome}.parquet"
        mdf.to_parquet(caminho, index=False)
    print(f"\nTrabalho reprodutivo salvo em: {ARQUIVO_TRABALHO_REPRODUTIVO.parent}")

    # --- Capital herdado ---
    ch = calcular_capital_herdado(df_part)
    for nome, mdf in ch.items():
        caminho = ARQUIVO_CAPITAL_HERDADO.parent / f"capital_herdado_{nome}.parquet"
        mdf.to_parquet(caminho, index=False)
    print(f"\nCapital herdado salvo em: {ARQUIVO_CAPITAL_HERDADO.parent}")


if __name__ == "__main__":
    main()
