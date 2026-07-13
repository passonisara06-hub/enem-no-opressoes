"""
visualizacoes.py — Funções de gráficos reutilizáveis (nível agregado)
====================================================================
Paleta construída com intencionalidade política:
- Tons de terra/ocre para grupos oprimidos
- Azuis frios para grupos privilegiados

Títulos e labels em português claro para público leigo.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from constants import (
    CORES, GRUPOS_PRINCIPAIS, ORDEM_GRUPOS, NOTAS_TODAS,
    MAPA_UF_NOME, MAPA_AREA_LABEL, MAPA_VARIAVEL_LABEL,
    COR_TERRA, COR_ACO, COR_DESTAQUE, COR_INSIGHT,
)

# Config padrão para todos os gráficos (download SVG, locale pt-BR)
_CONFIG_PADRAO = {
    "modeBarButtonsToAdd": ["downloadSVG"],
    "toImageButtonOptions": {"format": "svg", "filename": "enem_2025"},
    "locale": "pt-BR",
}


def _aplicar_layout_acessivel(fig: go.Figure, altura: int = 600) -> go.Figure:
    """Aplica layout padrão acessível: fonte legível, margens, config."""
    fig.update_layout(
        height=altura,
        font=dict(size=13, family="Inter, DM Sans, sans-serif"),
        margin=dict(l=80, r=40, t=60, b=60),
        plot_bgcolor="#FAFAFA",
        paper_bgcolor="#FFFFFF",
    )
    fig.update_xaxes(gridcolor="#E0E0E0")
    fig.update_yaxes(gridcolor="#E0E0E0")
    return fig


# ------------------------------------------------------------
# 1. Composição demográfica por UF (barras horizontais)
# ------------------------------------------------------------

def grafico_composicao_demografica(df: "pd.DataFrame", uf_destaque: str = None) -> go.Figure:
    """
    Barras horizontais mostrando a proporção de cada grupo do nó por estado.

    Espera DataFrame com colunas: uf, grupo_no, pct_grupo
    uf_destaque: sigla do UF para destacar (borda mais espessa)
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
        title="Quem faz o ENEM? — Perfil dos inscritos por estado",
        labels={
            "pct_grupo": "Proporção (%)",
            "uf": "Estado",
            "grupo_no": "Grupo",
        },
        barmode="stack",
    )
    fig.update_layout(
        legend_title_text="Grupo",
        xaxis_title="Proporção (%)",
        yaxis_title="",
    )
    _aplicar_layout_acessivel(fig, max(600, len(df_plot["uf"].unique()) * 25))
    fig.update_traces(hovertemplate="%{y}<br>%{data.name}: %{x:.1f}%<extra></extra>")
    return fig


# ------------------------------------------------------------
# 2. Notas por tipo de escola (barras)
# ------------------------------------------------------------

def grafico_notas_por_tipo_escola(df: "pd.DataFrame", area: str = "nota_media") -> go.Figure:
    """
    Notas médias por tipo de escola (Pública vs Privada) por estado.

    Espera DataFrame com colunas: uf, escola_tipo, e colunas de notas.
    """
    if area == "nota_media":
        col = "nota_media_geral_mean" if "nota_media_geral_mean" in df.columns else "nota_media"
        title_area = "Média geral das notas"
    else:
        col = f"media_{area.lower()}_mean" if f"media_{area.lower()}_mean" in df.columns else f"media_{area.lower()}"
        title_area = MAPA_AREA_LABEL.get(area, area)

    df_plot = df[df["escola_tipo"].isin(["Pública", "Privada"])].copy()

    fig = px.bar(
        df_plot,
        x=col,
        y="uf",
        color="escola_tipo",
        color_discrete_map=CORES,
        orientation="h",
        barmode="group",
        title=f"{title_area} — Escola pública × privada por estado",
        labels={
            col: "Nota média",
            "uf": "Estado",
            "escola_tipo": "Tipo de escola",
        },
    )
    fig.update_layout(legend_title_text="Tipo de escola")
    _aplicar_layout_acessivel(fig, max(600, len(df_plot["uf"].unique()) * 25))
    return fig


# ------------------------------------------------------------
# 3. Ausência por tipo de escola
# ------------------------------------------------------------

def grafico_ausencia_por_tipo(df: "pd.DataFrame") -> go.Figure:
    """
    Taxa de ausência por tipo de escola (Pública vs Privada) por estado.

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
        title="Quem falta à prova? — Ausência por tipo de escola",
        labels={
            "pct_ausente": "Taxa de ausência (%)",
            "uf": "Estado",
            "escola_tipo": "Tipo de escola",
        },
    )

    # Anotação contextual: comparação quando ambos os tipos estão presentes,
    # média simples quando só um tipo está selecionado
    tipos_presentes = df_plot["escola_tipo"].unique()
    if len(tipos_presentes) == 2:
        pub_mean = df_plot[df_plot["escola_tipo"] == "Pública"]["pct_ausente"].mean()
        pri_mean = df_plot[df_plot["escola_tipo"] == "Privada"]["pct_ausente"].mean()
        gap = pub_mean - pri_mean
        fig.add_annotation(
            text=f"Quem estuda em escola pública falta {gap:.1f} pp mais",
            xref="paper", yref="paper", x=0.95, y=1.05,
            showarrow=False, font=dict(size=14, color=COR_TERRA),
        )
    elif len(tipos_presentes) == 1:
        tipo = tipos_presentes[0]
        media = df_plot["pct_ausente"].mean()
        fig.add_annotation(
            text=f"Média: {media:.1f}% de ausência ({tipo})",
            xref="paper", yref="paper", x=0.95, y=1.05,
            showarrow=False, font=dict(size=14, color=COR_TERRA),
        )

    fig.update_layout(legend_title_text="Tipo de escola")
    _aplicar_layout_acessivel(fig, max(600, len(df_plot["uf"].unique()) * 25))
    return fig


# ------------------------------------------------------------
# 4. Heatmap de composição demográfica (raça × gênero por UF)
# ------------------------------------------------------------

def heatmap_composicao_uf(df: "pd.DataFrame") -> go.Figure:
    """
    Heatmap raça × gênero mostrando proporção de cada combinação por estado.

    Espera DataFrame com colunas: uf, grupo_no, pct_grupo
    """
    df_plot = df[df["grupo_no"].isin(GRUPOS_PRINCIPAIS)].copy()

    pivot = df_plot.pivot_table(
        index="uf", columns="grupo_no", values="pct_grupo", fill_value=0
    )
    cols_order = [c for c in ORDEM_GRUPOS if c in pivot.columns]
    pivot = pivot[cols_order]

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale=[
            [0, "#FFF8E7"],
            [0.5, "#CD853F"],
            [1, "#8B4513"],
        ],
        text=pivot.values.round(1),
        texttemplate="%{text:.1f}%",
        colorbar=dict(title="% dos inscritos"),
    ))

    fig.update_layout(
        title="Perfil dos inscritos por estado — proporção de cada grupo",
        xaxis_title="Grupo",
        yaxis_title="Estado",
    )
    _aplicar_layout_acessivel(fig, max(600, len(pivot) * 25))
    return fig


# ------------------------------------------------------------
# 5. Regressão ecológica — coeficientes
# ------------------------------------------------------------

def grafico_coeficientes_ecologicos(df: "pd.DataFrame") -> go.Figure:
    """
    Gráfico de coeficientes da regressão ecológica com intervalos de confiança.
    Variáveis renomeadas para português claro.

    Espera DataFrame com colunas: variavel, coef, std_err, p_valor
    """
    df_plot = df[~df["variavel"].str.contains("Intercept", case=False, na=False)].copy()
    df_plot = df_plot.sort_values("coef")

    # Renomear variáveis para labels legíveis
    df_plot["variavel_label"] = df_plot["variavel"].map(MAPA_VARIAVEL_LABEL).fillna(df_plot["variavel"])

    # Intervalo de confiança 95%
    df_plot["ic_inf"] = df_plot["coef"] - 1.96 * df_plot["std_err"]
    df_plot["ic_sup"] = df_plot["coef"] + 1.96 * df_plot["std_err"]

    # Cores por significância
    df_plot["cor"] = df_plot["p_valor"].apply(
        lambda p: COR_TERRA if p < 0.05 else "#A9A9A9"
    )

    fig = go.Figure()

    for _, row in df_plot.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["ic_inf"], row["ic_sup"]],
            y=[row["variavel_label"], row["variavel_label"]],
            mode="lines",
            line=dict(color=row["cor"], width=2),
            showlegend=False,
        ))

    fig.add_trace(go.Scatter(
        x=df_plot["coef"],
        y=df_plot["variavel_label"],
        mode="markers",
        marker=dict(size=10, color=df_plot["cor"]),
        name="Impacto no resultado",
    ))

    fig.add_vline(x=0, line_dash="dash", line_color="gray")

    # R² em linguagem clara
    if "r2" in df_plot.columns:
        r2 = df_plot["r2"].iloc[0]
        fig.add_annotation(
            text=f"Esses fatores explicam {r2*100:.0f}% das diferenças entre estados",
            xref="paper", yref="paper", x=0.02, y=0.98,
            showarrow=False, font=dict(size=12),
        )

    fig.update_layout(
        title="O que explica as diferenças entre estados?",
        xaxis_title="Impacto na nota média do estado",
        yaxis_title="",
    )
    _aplicar_layout_acessivel(fig, 400)
    return fig


# ------------------------------------------------------------
# 6. Gap público vs privado por UF
# ------------------------------------------------------------

def grafico_gap_escola(df: "pd.DataFrame") -> go.Figure:
    """
    Barras horizontais mostrando a diferença de notas entre escola pública e privada por estado.

    Espera DataFrame com colunas: uf, gap_publico_privado
    """
    df_plot = df.sort_values("gap_publico_privado", ascending=True)

    # Linha de referência na média nacional
    media_gap = df_plot["gap_publico_privado"].mean()

    fig = px.bar(
        df_plot,
        x="gap_publico_privado",
        y="uf",
        orientation="h",
        title="Diferença de notas: escola pública × privada por estado",
        labels={
            "gap_publico_privado": "Diferença (pontos)",
            "uf": "Estado",
        },
        color="gap_publico_privado",
        color_continuous_scale=[
            [0, "#4682B4"],
            [0.5, "#CD853F"],
            [1, "#8B4513"],
        ],
    )

    # Linha vertical na média
    fig.add_vline(
        x=media_gap, line_dash="dash", line_color=COR_DESTAQUE,
        annotation_text=f"Média: {media_gap:.0f} pontos",
        annotation_position="top right",
    )

    # Anotar extremos
    if len(df_plot) >= 2:
        menor = df_plot.iloc[0]
        maior = df_plot.iloc[-1]
        fig.add_annotation(
            text=f"Menor diferença: {menor['uf']} ({menor['gap_publico_privado']:.0f} pts)",
            xref="paper", yref="paper", x=0.02, y=0.02,
            showarrow=False, font=dict(size=11, color=COR_ACO),
        )
        fig.add_annotation(
            text=f"Maior diferença: {maior['uf']} ({maior['gap_publico_privado']:.0f} pts)",
            xref="paper", yref="paper", x=0.98, y=0.02,
            showarrow=False, font=dict(size=11, color=COR_TERRA),
        )

    fig.update_layout(showlegend=False)
    _aplicar_layout_acessivel(fig, max(600, len(df_plot) * 25))
    return fig


# ------------------------------------------------------------
# 7. NOVO — Mapa coroplético do Brasil
# ------------------------------------------------------------

def mapa_coropletico_brasil(df: "pd.DataFrame", coluna_valor: str, titulo: str,
                             cor_escala: list = None) -> go.Figure:
    """
    Mapa coroplético do Brasil colorido por estado.

    Espera DataFrame com colunas: uf + coluna_valor.
    coluna_valor: nome da coluna numérica para colorir o mapa.
    titulo: título do gráfico em português claro.
    cor_escala: lista [[pos, cor], ...] (opcional, padrão: terra → azul).
    """
    if cor_escala is None:
        cor_escala = [
            [0, "#4682B4"],     # Azul — valores baixos
            [0.5, "#CD853F"],   # Peru — médios
            [1, "#8B4513"],     # Siena — valores altos
        ]

    # Nomes completos para hover
    df_plot = df.copy()
    df_plot["estado"] = df_plot["uf"].map(MAPA_UF_NOME).fillna(df_plot["uf"])
    label_valor = coluna_valor.replace("_", " ").replace("pct", "%").strip()

    fig = px.choropleth(
        df_plot,
        geojson=None,  # será carregado via URL no dashboard
        locations="uf",
        locationmode="ISO-3",
        color=coluna_valor,
        hover_name="estado",
        hover_data={coluna_valor: ":.1f"},
        color_continuous_scale=cor_escala,
        title=titulo,
        labels={coluna_valor: label_valor},
    )

    fig.update_geos(
        visible=False, resolution=50,
        scope="south america",
        showcountries=True, countrycolor="#E0E0E0",
        showsubunits=True, subunitcolor="#E0E0E0",
    )

    _aplicar_layout_acessivel(fig, 550)
    return fig


# ------------------------------------------------------------
# 8. NOVO — Donut chart presença/ausência
# ------------------------------------------------------------

def grafico_ausencia_geral(pct_presente: float, pct_ausente: float) -> go.Figure:
    """
    Donut chart mostrando proporção de presentes e ausentes.

    pct_presente: porcentagem de presentes (0-100)
    pct_ausente: porcentagem de ausentes (0-100)
    """
    fig = go.Figure(data=[go.Pie(
        labels=["Compareceram aos dois dias", "Faltaram a pelo menos um dia"],
        values=[pct_presente, pct_ausente],
        hole=0.55,
        marker=dict(colors=[COR_ACO, COR_TERRA]),
        textinfo="label+percent",
        textfont=dict(size=14),
        hovertemplate="%{label}<br>%{value:.1f}%<extra></extra>",
    )])

    fig.update_layout(
        title="Comparecimento ao ENEM",
        showlegend=False,
        annotations=[dict(
            text=f"{pct_presente:.0f}%<br>presentes",
            x=0.5, y=0.5, font_size=20, font_color=COR_ACO,
            showarrow=False,
        )],
    )
    _aplicar_layout_acessivel(fig, 400)
    return fig


# ------------------------------------------------------------
# 9. NOVO — Scatter com reta de tendência
# ------------------------------------------------------------

def grafico_dispersao_tendencia(df: "pd.DataFrame", x: str, y: str,
                                 titulo: str, xlabel: str, ylabel: str) -> go.Figure:
    """
    Scatter plot com reta de tendência OLS. UFs como pontos.

    Espera DataFrame com colunas: uf, x, y
    xlabel/ylabel: rótulos em português claro.
    """
    fig = px.scatter(
        df, x=x, y=y, text="uf",
        trendline="ols",
        trendline_color_override=COR_DESTAQUE,
        title=titulo,
        labels={x: xlabel, y: ylabel},
        color_discrete_sequence=[COR_ACO],
    )

    # Rotular pontos
    fig.update_traces(
        textposition="top center",
        marker=dict(size=8, opacity=0.8),
        selector=dict(mode="markers+text"),
    )

    # Esconder equação da reta de tendência
    fig.data = [t for t in fig.data if not (hasattr(t, "mode") and t.mode == "lines") or True]

    _aplicar_layout_acessivel(fig, 500)
    return fig


# ------------------------------------------------------------
# 10. NOVO — Radar por área do conhecimento
# ------------------------------------------------------------

def grafico_radar_por_area(df_pub: "pd.DataFrame", df_pri: "pd.DataFrame",
                            uf: str) -> go.Figure:
    """
    Radar/spider chart comparando notas públicas vs privadas nas 5 áreas
    do conhecimento para um estado selecionado.

    df_pub, df_pri: DataFrames com 1 linha cada, com colunas de notas.
    Aceita tanto o formato metricas_desempenho (media_uf_nu_nota_*)
    quanto notas_tipo_escola (NU_NOTA_*_mean).
    uf: sigla do estado (para o título)
    """
    areas = ["CN", "CH", "LC", "MT", "Redação"]
    # Formato metricas_desempenho
    colunas_metricas = [
        "media_uf_nu_nota_cn", "media_uf_nu_nota_ch", "media_uf_nu_nota_lc",
        "media_uf_nu_nota_mt", "media_uf_nu_nota_redacao",
    ]
    # Formato notas_tipo_escola
    colunas_notas = [
        "NU_NOTA_CN_mean", "NU_NOTA_CH_mean", "NU_NOTA_LC_mean",
        "NU_NOTA_MT_mean", "NU_NOTA_REDACAO_mean",
    ]
    labels = [
        "Ciências da\nNatureza", "Ciências\nHumanas", "Linguagens e\nCódigos",
        "Matemática", "Redação",
    ]

    # Detectar formato disponível
    if all(c in df_pub.columns for c in colunas_metricas):
        colunas = colunas_metricas
    elif all(c in df_pub.columns for c in colunas_notas):
        colunas = colunas_notas
    else:
        # Fallback: tentar qualquer formato disponível
        colunas = []
        for cm, cn in zip(colunas_metricas, colunas_notas):
            if cm in df_pub.columns:
                colunas.append(cm)
            elif cn in df_pub.columns:
                colunas.append(cn)

    vals_pub = [df_pub.iloc[0][c] if c in df_pub.columns else 0 for c in colunas]
    vals_pri = [df_pri.iloc[0][c] if c in df_pri.columns else 0 for c in colunas]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=vals_pri,
        theta=labels,
        fill="toself",
        name="Escola privada",
        line=dict(color=COR_ACO),
        opacity=0.6,
    ))

    fig.add_trace(go.Scatterpolar(
        r=vals_pub,
        theta=labels,
        fill="toself",
        name="Escola pública",
        line=dict(color=COR_TERRA),
        opacity=0.6,
    ))

    nome_uf = MAPA_UF_NOME.get(uf, uf)
    fig.update_layout(
        title=f"Notas por área do conhecimento — {nome_uf}",
        polar=dict(radialaxis=dict(visible=True, range=[400, 700])),
        showlegend=True,
        legend=dict(x=0.01, y=0.01),
    )
    _aplicar_layout_acessivel(fig, 450)
    return fig


# ------------------------------------------------------------
# 11. NOVO — Ranking de estados (barras horizontais ordenadas)
# ------------------------------------------------------------

def grafico_ranking_uf(df: "pd.DataFrame", coluna: str, titulo: str,
                        xlabel: str, uf_destaque: str = None,
                        cor_maior: str = None, cor_menor: str = None) -> go.Figure:
    """
    Barras horizontais ordenadas mostrando ranking de estados por uma métrica.

    Espera DataFrame com colunas: uf, coluna (numérica).
    uf_destaque: sigla do UF para destacar.
    cor_maior/cor_menor: cores para os extremos (opcional).
    """
    df_plot = df.dropna(subset=[coluna]).sort_values(coluna, ascending=True).copy()

    if cor_maior is None:
        cor_maior = COR_TERRA
    if cor_menor is None:
        cor_menor = COR_ACO

    # Cor de cada barra: destacar UF selecionado
    if uf_destaque and uf_destaque in df_plot["uf"].values:
        cores = [COR_DESTAQUE if uf == uf_destaque else "#D3D3D3"
                 for uf in df_plot["uf"]]
    else:
        # Gradual: menor valor = azul, maior = terra
        vmin = df_plot[coluna].min()
        vmax = df_plot[coluna].max()
        if vmax > vmin:
            norm = (df_plot[coluna] - vmin) / (vmax - vmin)
        else:
            norm = pd.Series(0.5, index=df_plot.index)
        cores = [cor_menor if n < 0.5 else cor_maior for n in norm]

    nome_uf = MAPA_UF_NOME  # para hover

    fig = go.Figure(go.Bar(
        x=df_plot[coluna],
        y=[nome_uf.get(u, u) for u in df_plot["uf"]],
        orientation="h",
        marker_color=cores,
        hovertemplate="%{y}<br>" + xlabel + ": %{x:.1f}<extra></extra>",
    ))

    fig.update_layout(
        title=titulo,
        xaxis_title=xlabel,
        yaxis_title="",
    )
    _aplicar_layout_acessivel(fig, max(500, len(df_plot) * 22))
    return fig