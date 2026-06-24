"""
inferencial.py — Análise estatística inferencial (nível agregado)
================================================================
Como os microdados de 2025 estão divididos em PARTICIPANTES e RESULTADOS
sem chave de junção individual (LGPD), a análise inferencial é realizada
no nível ecológico (UF), cruzando composição demográfica com desempenho.

ADVERTÊNCIA METODOLÓGICA: Correlações ecológicas não implicam relações
individuais (falácia ecológica). Os resultados devem ser interpretados
como indicadores de desigualdades estruturais regionais, não como
efeitos individuais.

Uso:
    python src/inferencial.py
Saída:
    data/processed/regressao_ecologica.parquet
    data/processed/gaps_regionais.parquet
    data/processed/testes_kruskal.parquet
"""

import warnings
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
from constants import (
    ARQUIVO_METRICAS_DEMO, ARQUIVO_METRICAS_DESEMP,
    ARQUIVO_REGRESSAO_ECO, ARQUIVO_GAPS_REGIONAIS, ARQUIVO_TESTES_KRUSKAL,
    NOTAS_TODAS, GRUPOS_PRINCIPAIS,
)

# Suprimir apenas FutureWarnings, não alertas de convergência
warnings.filterwarnings("ignore", category=FutureWarning)


def regressao_ecologica(df_demo: pd.DataFrame, df_desemp: pd.DataFrame) -> pd.DataFrame:
    """
    Regressão ecológica: nota média do UF ~ composição demográfica + tipo de escola + UF.

    Variáveis independentes:
    - pct_mulher_negra: % de mulheres negras no UF
    - pct_negra: % de população negra no UF
    - pct_escola_publica: % de alunos em escola pública no UF (proxy)
    - renda_media: renda média no UF

    A interpretação segue Saffioti: a posição estrutural no nó (capturada
    pela composição demográfica regional) é uma determinação social, não
    um atributo individual.
    """
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
    except ImportError:
        print("AVISO: statsmodels não instalado. Pulando regressão ecológica.")
        return pd.DataFrame()

    print("Executando regressão ecológica...")

    # Preparar dados agregados: um registro por UF
    # Pivotar métricas demográficas para wide
    demo_wide = df_demo.pivot_table(
        index="uf", columns="grupo_no", values="pct_grupo", fill_value=0
    ).reset_index()

    # Adicionar renda média e composição racial
    demo_agg = df_demo.groupby("uf").agg(
        pct_negra=("pct_negra", "first"),
        pct_branca=("pct_branca", "first"),
        pct_feminino=("pct_feminino", "first"),
        pct_mulher_negra=("pct_mulher_negra", "first"),
        renda_media=("renda_media", "first"),
    ).reset_index()

    # Merge com métricas de desempenho
    df_agg = df_desemp.merge(demo_agg, on="uf", how="inner")

    if len(df_agg) < 5:
        print("  → Poucos UFs para regressão confiável. Pulando.")
        return pd.DataFrame()

    # Regressão ecológica: nota_media_uf ~ pct_mulher_negra + renda_media + pct_presente_uf
    # Referência: UFs com menor % de população oprimida
    formula = "nota_media_uf ~ pct_mulher_negra + renda_media + pct_presente_uf"

    try:
        modelo = smf.ols(formula, data=df_agg).fit()
        coefs = pd.DataFrame({
            "variavel": modelo.params.index,
            "coef": modelo.params.values,
            "std_err": modelo.bse.values,
            "p_valor": modelo.pvalues.values,
            "ic_inf": modelo.conf_int()[0].values,
            "ic_sup": modelo.conf_int()[1].values,
        })
        coefs["r2"] = modelo.rsquared
        coefs["r2_adj"] = modelo.rsquared_adj
        coefs["n_obs"] = modelo.nobs
        coefs["f_stat"] = modelo.fvalue
        coefs["f_pvalor"] = modelo.f_pvalue

        print(f"  → R² = {modelo.rsquared:.3f}, R² adj = {modelo.rsquared_adj:.3f}")
        print(f"  → F-statistic = {modelo.fvalue:.2f}, p = {modelo.f_pvalue:.4f}")
        return coefs
    except Exception as e:
        print(f"  → Erro na regressão: {e}")
        return pd.DataFrame()


def teste_kruskal_agregado(df_desemp: pd.DataFrame) -> pd.DataFrame:
    """
    Teste de Kruskal-Wallis agregado: compara notas médias entre UFs,
    agrupados por tercils de composição demográfica.

    Como não podemos comparar grupos individuais (LGPD), comparamos UFs
    com maior e menor proporção de grupos oprimidos.
    """
    print("Executando testes de Kruskal-Wallis agregados...")

    resultados = []

    # Para cada área de nota, comparar UFs agrupados por tercil de ausência
    # (proxy para desigualdade estrutural)
    col_nota = "nota_media_uf"
    if col_nota not in df_desemp.columns:
        print(f"  → Coluna {col_nota} não encontrada. Pulando.")
        return pd.DataFrame()

    # Dividir UFs em tercis de taxa de ausência
    df_desemp["tercil_ausencia"] = pd.qcut(
        df_desemp["pct_ausente_uf"], q=3, labels=["Baixa", "Média", "Alta"], duplicates="drop"
    )

    grupos = [g[col_nota].dropna().values for _, g in df_desemp.groupby("tercil_ausencia")]

    if len(grupos) >= 2 and all(len(g) > 0 for g in grupos):
        stat, p_valor = stats.kruskal(*grupos)
        resultados.append({
            "area": "nota_media_geral",
            "h_stat": stat,
            "p_valor": p_valor,
            "comparacao": "Tercis de taxa de ausência",
            "n_grupos": len(grupos),
        })
        print(f"  → nota_media_geral: H={stat:.2f}, p={p_valor:.4f}")

    # Também comparar público vs privado
    col_gap = "gap_publico_privado"
    if col_gap in df_desemp.columns:
        stat_gap, p_gap = stats.mannwhitneyu(
            df_desemp[col_gap].dropna(),
            [0] * len(df_desemp[col_gap].dropna()),  # teste se gap != 0
            alternative="greater",
        ) if len(df_desemp[col_gap].dropna()) > 0 else (np.nan, np.nan)

        resultados.append({
            "area": "gap_publico_privado",
            "h_stat": stat_gap,
            "p_valor": p_gap,
            "comparacao": "Gap público vs privado por UF",
            "n_grupos": 2,
        })

    return pd.DataFrame(resultados)


def gaps_regionais(df_desemp: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula gaps regionais: diferença de notas entre escolas públicas e privadas
    por UF, e correlação entre composição demográfica e desempenho.
    """
    print("Calculando gaps regionais...")

    # Gap público vs privado já calculado em metricas_desempenho
    gaps = df_desemp[["uf", "gap_publico_privado", "nota_media_uf", "pct_ausente_uf"]].copy()

    # Estatísticas descritivas
    if "gap_publico_privado" in gaps.columns:
        gap_mean = gaps["gap_publico_privado"].mean()
        gap_median = gaps["gap_publico_privado"].median()
        gap_min = gaps["gap_publico_privado"].min()
        gap_max = gaps["gap_publico_privado"].max()
        print(f"  → Gap público vs privado:")
        print(f"     Média: {gap_mean:.1f} pontos")
        print(f"     Mediana: {gap_median:.1f} pontos")
        print(f"     Mínimo: {gap_min:.1f} (UF: {gaps.loc[gaps['gap_publico_privado'].idxmin(), 'uf']})")
        print(f"     Máximo: {gap_max:.1f} (UF: {gaps.loc[gaps['gap_publico_privado'].idxmax(), 'uf']})")

    return gaps


def main():
    """Pipeline inferencial: lê métricas e executa análises agregadas."""
    print("Carregando métricas...")
    df_demo = pd.read_parquet(ARQUIVO_METRICAS_DEMO)
    df_desemp = pd.read_parquet(ARQUIVO_METRICAS_DESEMP)

    # --- Regressão ecológica ---
    coefs = regressao_ecologica(df_demo, df_desemp)
    if not coefs.empty:
        coefs.to_parquet(ARQUIVO_REGRESSAO_ECO, index=False)
        print(f"\nRegressão ecológica salva em: {ARQUIVO_REGRESSAO_ECO}")

    # --- Testes de Kruskal-Wallis agregados ---
    testes = teste_kruskal_agregado(df_desemp)
    if not testes.empty:
        testes.to_parquet(ARQUIVO_TESTES_KRUSKAL, index=False)
        print(f"\nTestes Kruskal-Wallis salvos em: {ARQUIVO_TESTES_KRUSKAL}")

    # --- Gaps regionais ---
    gaps = gaps_regionais(df_desemp)
    gaps.to_parquet(ARQUIVO_GAPS_REGIONAIS, index=False)
    print(f"\nGaps regionais salvos em: {ARQUIVO_GAPS_REGIONAIS}")


if __name__ == "__main__":
    main()