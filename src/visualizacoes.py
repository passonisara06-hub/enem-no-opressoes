"""
visualizacoes.py — Funções de gráficos reutilizáveis (nível agregado)
====================================================================
Paleta construída com intencionalidade política:
- Tons de terra/ocre para grupos oprimidos
- Azuis frios para grupos privilegiados

NOTA: Como a análise é agregada (LGPD), os gráficos mostram
proporções demográficas e desempenho por tipo de escola e UF,
não notas por grupo individual.
"""

import plotly.express as px
import plotly.graph_objects as go
from constants import CORES, GRUPOS_PRINCIPAIS, ORDEM_GRUPOS, NOTAS_TODAS


# ------------------------------------------------------------
# 1. Composição demográfica por UF (barras horizontais)
# ------------------------------------------------------------

def grafico_composicao_demografica(df: "pd.DataFrame") -> go.Figure:
    """
    Barras horizontais mostrando a proporção de cada grupo do nó por UF.

    Espera DataFrame com colunas: uf, grupo_no, pct_grupo
    """
    df_plot = df[df["grupo_no"].isin(GRUPOS_PRINCIPAIS)].copy()
    df_plot["grupo_no"] = df_plot["grupo_no"].astype(
        pd.CategoricalDtype(categories=ORDEM_GRUPOS, ordered=True)
    )
    df_plot = df_plot.sort_values(["uf", "grupo_no"])

    fig = px.bar(
        df_plot,
        x="pct_grupo",
        y="uf",
        color="grupo_no",
        color_discrete_map=CORES,
        orientation="h",
        title="Composição demográfica por UF — Nó de Opressões",
        labels={"pct_grupo": "Proporção (%)", "uf": "UF", "grupo_no": "Grupo"},
        barmode="stack",
    )
    fig.update_layout(
        height=max(600, len(df_plot["uf"].unique()) * 25),
        legend_title_text="Grupo estrutural",
        xaxis_title="Proporção (%)",
        yaxis_title="",
    )
    return fig


# ------------------------------------------------------------
# 2. Notas por tipo de escola (barras)
# ------------------------------------------------------------

def grafico_notas_por_tipo_escola(df: "pd.DataFrame", area: str = "nota_media") -> go.Figure:
    """
    Notas médias por tipo de escola (Pública vs Privada) por UF.

    Espera DataFrame com colunas: uf, escola_tipo, e colunas de notas.
    """
    if area == "nota_media":
        col = "nota_media_geral_mean" if "nota_media_geral_mean" in df.columns else "nota_media"
        title_area = "Nota média geral"
    else:
        col = f"media_{area.lower()}_mean" if f"media_{area.lower()}_mean" in df.columns else f"media_{area.lower()}"
        title_area = area.replace("NU_NOTA_", "")

    df_plot = df[df["escola_tipo"].isin(["Pública", "Privada"])].copy()

    fig = px.bar(
        df_plot,
        x=col,
        y="uf",
        color="escola_tipo",
        color_discrete_map=CORES,
        orientation="h",
        barmode="group",
        title=f"{title_area} — Pública vs Privada por UF",
        labels={col: "Nota", "uf": "UF", "escola_tipo": "Tipo de escola"},
    )
    fig.update_layout(
        height=max(600, len(df_plot["uf"].unique()) * 25),
        legend_title_text="Tipo de escola",
    )
    return fig


# ------------------------------------------------------------
# 3. Ausência por tipo de escola
# ------------------------------------------------------------

def grafico_ausencia_por_tipo(df: "pd.DataFrame") -> go.Figure:
    """
    Taxa de ausência por tipo de escola (Pública vs Privada) por UF.

    Espera DataFrame com colunas: uf, escola_tipo, pct_ausente
    """
    df_plot = df[df["escola_tipo"].isin(["Pública", "Privada"])].copy()

    fig = px.bar(
        df_plot,
        x="pct_ausente",
        y="uf",
        color="escola_tipo",
        color_discrete_map=CORES,
        orientation="h",
        barmode="group",
        title="Taxa de ausência — Pública vs Privada por UF",
        labels={"pct_ausente": "Ausência (%)", "uf": "UF", "escola_tipo": "Tipo de escola"},
    )

    # Anotação com gap médio
    if len(df_plot) > 0:
        pub_mean = df_plot[df_plot["escola_tipo"] == "Pública"]["pct_ausente"].mean()
        pri_mean = df_plot[df_plot["escola_tipo"] == "Privada"]["pct_ausente"].mean()
        gap = pub_mean - pri_mean
        fig.add_annotation(
            text=f"Gap médio: {gap:.1f} pp",
            xref="paper", yref="paper", x=0.95, y=1.05,
            showarrow=False, font=dict(size=14, color="#8B4513"),
        )

    fig.update_layout(
        height=max(600, len(df_plot["uf"].unique()) * 25),
        legend_title_text="Tipo de escola",
    )
    return fig


# ------------------------------------------------------------
# 4. Heatmap de composição demográfica (raça × gênero por UF)
# ------------------------------------------------------------

def heatmap_composicao_uf(df: "pd.DataFrame") -> go.Figure:
    """
    Heatmap raça × gênero mostrando proporção de cada combinação por UF.

    Espera DataFrame com colunas: uf, grupo_no, pct_grupo
    """
    df_plot = df[df["grupo_no"].isin(GRUPOS_PRINCIPAIS)].copy()

    # Pivotar para formato wide
    pivot = df_plot.pivot_table(
        index="uf", columns="grupo_no", values="pct_grupo", fill_value=0
    )

    # Reordenar colunas
    cols_order = [c for c in ORDEM_GRUPOS if c in pivot.columns]
    pivot = pivot[cols_order]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale=[
            [0, "#FFF8E7"],    # Creme claro
            [0.5, "#CD853F"],   # Peru
            [1, "#8B4513"],     # Siena escuro
        ],
        text=pivot.values.round(1),
        texttemplate="%{text:.1f}%",
        colorbar=dict(title="% do UF"),
    ))

    fig.update_layout(
        title="Composição demográfica por UF — Nó de Opressões (% do total de inscritos)",
        xaxis_title="Grupo estrutural",
        yaxis_title="UF",
        height=max(600, len(pivot) * 25),
    )
    return fig


# ------------------------------------------------------------
# 5. Regressão ecológica — coeficientes
# ------------------------------------------------------------

def grafico_coeficientes_ecologicos(df: "pd.DataFrame") -> go.Figure:
    """
    Gráfico de coeficientes da regressão ecológica com intervalos de confiança.

    Espera DataFrame com colunas: variavel, coef, std_err, p_valor
    """
    # Filtrar intercepto
    df_plot = df[~df["variavel"].str.contains("Intercept", case=False, na=False)].copy()
    df_plot = df_plot.sort_values("coef")

    # Intervalo de confiança 95%
    df_plot["ic_inf"] = df_plot["coef"] - 1.96 * df_plot["std_err"]
    df_plot["ic_sup"] = df_plot["coef"] + 1.96 * df_plot["std_err"]

    # Cores por significância
    df_plot["cor"] = df_plot["p_valor"].apply(
        lambda p: "#8B4513" if p < 0.05 else "#A9A9A9"
    )

    fig = go.Figure()

    for _, row in df_plot.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["ic_inf"], row["ic_sup"]],
            y=[row["variavel"], row["variavel"]],
            mode="lines",
            line=dict(color=row["cor"], width=2),
            showlegend=False,
        ))

    fig.add_trace(go.Scatter(
        x=df_plot["coef"],
        y=df_plot["variavel"],
        mode="markers",
        marker=dict(size=10, color=df_plot["cor"]),
        name="Coeficiente",
    ))

    # Linha vertical em 0
    fig.add_vline(x=0, line_dash="dash", line_color="gray")

    # R² e F
    if "r2" in df_plot.columns:
        r2 = df_plot["r2"].iloc[0]
        fig.add_annotation(
            text=f"R² = {r2:.3f}",
            xref="paper", yref="paper", x=0.02, y=0.98,
            showarrow=False, font=dict(size=12),
        )

    fig.update_layout(
        title="Regressão ecológica — Coeficientes (nota média por UF)",
        xaxis_title="Coeficiente",
        yaxis_title="",
        height=400,
    )
    return fig


# ------------------------------------------------------------
# 6. Gap público vs privado por UF
# ------------------------------------------------------------

def grafico_gap_escola(df: "pd.DataFrame") -> go.Figure:
    """
    Barras horizontais mostrando o gap de notas entre escola pública e privada por UF.

    Espera DataFrame com colunas: uf, gap_publico_privado
    """
    df_plot = df.sort_values("gap_publico_privado", ascending=True)

    fig = px.bar(
        df_plot,
        x="gap_publico_privado",
        y="uf",
        orientation="h",
        title="Gap entre escola pública e privada por UF (pontos na nota média)",
        labels={"gap_publico_privado": "Gap (pontos)", "uf": "UF"},
        color="gap_publico_privado",
        color_continuous_scale=[
            [0, "#4682B4"],     # Azul — gap menor
            [0.5, "#CD853F"],   # Peru — gap médio
            [1, "#8B4513"],     # Siena — gap maior
        ],
    )
    fig.update_layout(
        height=max(600, len(df_plot) * 25),
        showlegend=False,
    )
    return fig