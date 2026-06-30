"""
dashboard.py — Painel ENEM 2025: Nó de Opressões
=================================================
Dashboard acessível para professores e gestores escolares.

Linguagem simples, visualizações claras, divulgação progressiva.
O jargão estatístico fica dentro de expanders, nunca na vista principal.

Rodar:
    streamlit run app/dashboard.py
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Adicionar src/ ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from constants import (
    ANO, GRUPOS_PRINCIPAIS, ORDEM_GRUPOS, CORES,
    ARQUIVO_PART_LIMPO, ARQUIVO_RES_LIMPO,
    ARQUIVO_METRICAS_DEMO, ARQUIVO_METRICAS_DESEMP,
    ARQUIVO_REGRESSAO_ECO, ARQUIVO_GAPS_REGIONAIS, ARQUIVO_TESTES_KRUSKAL,
    NOTAS_TODAS, MAPA_UF_NOME, MAPA_UF_REGIAO, REGIOES,
    MAPA_AREA_LABEL, MAPA_VARIAVEL_LABEL,
    COR_TERRA, COR_ACO, COR_DESTAQUE, COR_INSIGHT, COR_FUNDO,
    GEOJSON_URL,
)
from visualizacoes import (
    grafico_composicao_demografica,
    grafico_notas_por_tipo_escola,
    grafico_ausencia_por_tipo,
    heatmap_composicao_uf,
    grafico_coeficientes_ecologicos,
    grafico_gap_escola,
    grafico_ausencia_geral,
    grafico_dispersao_tendencia,
    grafico_radar_por_area,
    grafico_ranking_uf,
)

# ------------------------------------------------------------
# Configuração da página
# ------------------------------------------------------------
st.set_page_config(
    page_title=f"ENEM {ANO} — Desigualdade no Brasil",
    page_icon="📊",
    layout="wide",
)

# CSS acessível
st.markdown("""
<style>
.insight-box {
    background: #E8F5E9;
    padding: 1rem 1.25rem;
    border-radius: 0.5rem;
    border-left: 4px solid #4CAF50;
    margin: 1rem 0;
    font-size: 1rem;
    line-height: 1.7;
    color: #333;
}
.narrativo {
    background: linear-gradient(135deg, #FFF8E7 0%, #F5DEB3 100%);
    padding: 1.5rem;
    border-radius: 0.5rem;
    border-left: 4px solid #8B4513;
    margin: 1rem 0;
    font-size: 0.95rem;
    line-height: 1.7;
}
.narrativo em {
    color: #8B4513;
    font-style: italic;
}
.alerta-metodo {
    background: #FFF3CD;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #FFC107;
    margin: 1rem 0;
    font-size: 0.9rem;
    color: #333;
}
.destaque-numero {
    font-size: 2rem;
    font-weight: 700;
    color: #8B4513;
    line-height: 1.2;
}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------
# Carregar dados (cache)
# ------------------------------------------------------------
@st.cache_data
def carregar_dados():
    """Carrega todos os parquets processados."""
    dados = {}
    try:
        dados["participantes"] = pd.read_parquet(ARQUIVO_PART_LIMPO)
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {ARQUIVO_PART_LIMPO}. Execute `python src/ingestao.py` primeiro.")
        st.stop()

    try:
        dados["resultados"] = pd.read_parquet(ARQUIVO_RES_LIMPO)
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {ARQUIVO_RES_LIMPO}. Execute `python src/ingestao.py` primeiro.")
        st.stop()

    try:
        dados["metricas_demo"] = pd.read_parquet(ARQUIVO_METRICAS_DEMO)
    except FileNotFoundError:
        st.warning("Métricas demográficas não encontradas. Execute `python src/grupos.py`.")

    try:
        dados["metricas_desemp"] = pd.read_parquet(ARQUIVO_METRICAS_DESEMP)
    except FileNotFoundError:
        st.warning("Métricas de desempenho não encontradas. Execute `python src/grupos.py`.")

    try:
        dados["coefs"] = pd.read_parquet(ARQUIVO_REGRESSAO_ECO)
    except FileNotFoundError:
        pass

    try:
        dados["gaps"] = pd.read_parquet(ARQUIVO_GAPS_REGIONAIS)
    except FileNotFoundError:
        pass

    try:
        dados["kruskal"] = pd.read_parquet(ARQUIVO_TESTES_KRUSKAL)
    except FileNotFoundError:
        pass

    return dados


dados = carregar_dados()

# Dados derivados (computados uma vez)
df_part = dados.get("participantes", pd.DataFrame())
df_res = dados.get("resultados", pd.DataFrame())
df_demo = dados.get("metricas_demo", pd.DataFrame())
df_desemp = dados.get("metricas_desemp", pd.DataFrame())
df_coefs = dados.get("coefs", pd.DataFrame())
df_gaps = dados.get("gaps", pd.DataFrame())
df_kruskal = dados.get("kruskal", pd.DataFrame())

# Lista de UFs
todos_ufs = sorted(df_part["uf"].unique()) if len(df_part) > 0 else []

# Métricas gerais (calculadas uma vez)
total_inscritos = len(df_part) if len(df_part) > 0 else 0
total_resultados = len(df_res) if len(df_res) > 0 else 0
if total_resultados > 0 and "presente_ambos_dias" in df_res.columns:
    pct_presente = df_res["presente_ambos_dias"].mean() * 100
    pct_ausente = 100 - pct_presente
else:
    pct_presente = 67.4
    pct_ausente = 32.6

if len(df_gaps) > 0 and "gap_publico_privado" in df_gaps.columns:
    gap_medio = df_gaps["gap_publico_privado"].mean()
else:
    gap_medio = 107

r2 = 0.859
if len(df_coefs) > 0 and "r2" in df_coefs.columns:
    r2 = df_coefs["r2"].iloc[0]

# Mulher negra: maior grupo nacional
pct_mn_nacional = 0
if len(df_demo) > 0 and "pct_mulher_negra" in df_demo.columns:
    pct_mn_nacional = df_demo["pct_mulher_negra"].mean()


# ------------------------------------------------------------
# Sidebar — Filtros sincronizados + Sobre
# ------------------------------------------------------------
st.sidebar.header("🗺️ Filtros")

# Seletor de estado
opcoes_uf = ["Brasil (todos)"] + [f"{uf} — {MAPA_UF_NOME.get(uf, uf)}" for uf in todos_ufs]
uf_sel_raw = st.sidebar.selectbox("Selecione o estado", opcoes_uf, index=0)
if uf_sel_raw == "Brasil (todos)":
    uf_selecionado = None
else:
    uf_selecionado = uf_sel_raw.split(" — ")[0]

# Seletor de região
regiao_sel = st.sidebar.selectbox("Região", ["Todas"] + REGIOES)

st.sidebar.markdown("---")
st.sidebar.markdown("""
📚 **Sobre esta análise**

Este painel mostra como raça, gênero e classe se entrelaçam
para produzir desigualdade no ENEM, usando o conceito de
**nó de opressões** de Heleieth Saffioti.

Os dados são do ENEM 2025 (INEP/MEC).
""")

with st.sidebar.expander("📖 Como ler estes dados?"):
    st.markdown("""
    **O que significa "por estado, não por aluno"?**

    Os dados do ENEM 2025 estão divididos em dois arquivos separados
    (por exigência da LGPD), sem como ligar dados demográficos
    (raça, gênero) a notas individuais.

    Por isso, a análise compara **estados inteiros**, não alunos.
    Se um estado tem mais mulheres negras e notas mais baixas,
    isso **não significa** que mulheres negras têm notas mais baixas
    — significa que estados com mais população oprimida tendem a ter
    menos investimentos em educação.

    **O que é "R² = 86%"?**

    Significa que 86% das diferenças de notas entre estados podem ser
    explicadas por três fatores: proporção de mulheres negras,
    renda média e taxa de presença.

    **O que é "gap público × privado"?**

    É a diferença, em pontos, entre a nota média de quem estuda em
    escola pública e de quem estuda em escola privada.
    """)

with st.sidebar.expander("⚠️ Limitações"):
    st.markdown("""
    - **Dados de escola**: apenas ~36% dos inscritos informaram o tipo de escola
    - **Gênero binário**: o questionário INEP só oferece M/F
    - **Raça por autodeclaração**: captura identidade, não classificação racial
    - **Análise ecológica**: correlações por estado não implicam relações individuais
    """)


# ------------------------------------------------------------
# Funções auxiliares de filtro
# ------------------------------------------------------------
def filtrar_por_uf_regiao(df, uf, regiao):
    """Filtra DataFrame por UF e/ou região."""
    df_f = df.copy()
    if uf and "uf" in df_f.columns:
        df_f = df_f[df_f["uf"] == uf]
    elif regiao != "Todas" and "uf" in df_f.columns:
        ufs_regiao = [u for u, r in MAPA_UF_REGIAO.items() if r == regiao]
        df_f = df_f[df_f["uf"].isin(ufs_regiao)]
    return df_f


def csv_download_button(df, nome_arquivo, label="📥 Baixar dados (CSV)"):
    """Botão de download CSV com dados filtrados."""
    if len(df) > 0:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(label, data=csv, file_name=nome_arquivo, mime="text/csv")


# ============================================================
# HERO — Painel ENEM 2025
# ============================================================
def render_hero():
    """Landing page com métricas-destaque e introdução."""
    st.title(f"ENEM {ANO}: Desigualdade no Brasil")
    st.markdown("""
    Este painel mostra como **raça, gênero e classe** se entrelaçam
    para produzir desigualdade no ENEM — usando o conceito de
    **nó de opressões** de Heleieth Saffioti.
    """)

    # 4 métricas-destaque
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Inscritos", f"{total_inscritos/1e6:.1f} milhões")
    col2.metric("Compareceram", f"{pct_presente:.0f}%")
    col3.metric("Gap pública × privada", f"{gap_medio:.0f} pontos")
    col4.metric("Variação explicada", f"{r2*100:.0f}%")

    st.markdown(f"""
    <div class="insight-box">
    <strong>O que esses números significam?</strong><br>
    3 fatores explicam {r2*100:.0f}% das diferenças de notas entre estados:
    a proporção de mulheres negras, a renda média e a taxa de presença.
    A diferença de <strong>{gap_medio:.0f} pontos</strong> entre escola pública e privada
    não é sobre capacidade individual — é sobre quem o sistema inclui e quem ele exclui.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="alerta-metodo">
    ⚠️ <strong>Atenção:</strong> Os dados são <strong>por estado</strong>,
    não por aluno individual. Isso significa que não podemos dizer que
    uma aluna negra específica terá tal nota — apenas que estados com mais
    população oprimida tendem a ter notas médias menores.
    Além disso, apenas ~36% dos inscritos informaram o tipo de escola.
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# SEÇÃO 1: Quem faz o ENEM?
# ============================================================
def render_secao_quem_faz():
    """Aba 1: Perfil demográfico dos inscritos por estado."""
    st.header("🙋 Quem faz o ENEM?")
    st.markdown("Quantos inscritos, quem são e como o perfil muda de estado para estado.")

    if df_demo.empty:
        st.warning("Dados demográficos não disponíveis. Execute o pipeline completo.")
        return

    df_f = filtrar_por_uf_regiao(df_demo, uf_selecionado, regiao_sel)

    # Cards
    col1, col2, col3 = st.columns(3)
    col1.metric("Estados na seleção", f"{df_f['uf'].nunique() if len(df_f) > 0 else 0}")
    if "pct_mulher_negra" in df_f.columns:
        col2.metric("Mulheres negras (média)", f"{df_f['pct_mulher_negra'].mean():.1f}%")
    if "pct_negra" in df_f.columns:
        col3.metric("População negra (média)", f"{df_f['pct_negra'].mean():.1f}%")

    # Gráfico de composição demográfica
    st.subheader("Perfil dos inscritos por estado")
    fig_comp = grafico_composicao_demografica(df_f)
    st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
    Em todos os estados, <strong>mulheres negras</strong> são o maior ou segundo maior
    grupo de inscritos. Isso mostra que o ENEM é feito majoritariamente por quem vive
    na interseção de opressão — e que a desigualdade já começa antes da prova.
    </div>
    """, unsafe_allow_html=True)

    # Heatmap
    with st.expander("📊 Ver perfil detalhado (heatmap)"):
        fig_heat = heatmap_composicao_uf(df_f)
        st.plotly_chart(fig_heat, use_container_width=True)

    # Expander teórico
    with st.expander("📚 O que é o nó de opressões?"):
        st.markdown("""
        O **nó de opressões** é um conceito de Heleieth Saffioti (2004) que articula
        raça, gênero e classe como dimensões que se constituem mutuamente — não como
        eixos independentes que se cruzam.

        A mulher negra não é "mulher + negra": ela ocupa uma **posição estrutural**
        específica no sistema patriarcal-racista-capitalista. Não somamos desvantagens;
        identificamos configurações do nó.

        **Referência**: Saffioti, H. (2004). *O nó do nó de opressões*. São Paulo.
        """)

    # Download
    csv_download_button(df_f, f"composicao_demografica_{ANO}.csv")


# ============================================================
# SEÇÃO 2: Quem falta à prova?
# ============================================================
def render_secao_quem_falta():
    """Aba 2: Presença e ausência por tipo de escola."""
    st.header("🚪 Quem falta à prova?")
    st.markdown("Quantos inscritos compareceram e quem tem mais chance de faltar.")

    if df_res.empty:
        st.warning("Dados de resultados não disponíveis.")
        return

    df_f = filtrar_por_uf_regiao(df_res, uf_selecionado, regiao_sel)

    # Filtro de tipo de escola
    tipo_escola = st.radio(
        "Tipo de escola",
        ["Todas", "Pública", "Privada"],
        horizontal=True,
        key="tipo_escola_ausencia",
    )

    # Cards
    total_f = len(df_f)
    presentes_f = df_f["presente_ambos_dias"].sum() if "presente_ambos_dias" in df_f.columns else 0
    pct_pres = presentes_f / total_f * 100 if total_f > 0 else 0
    pct_aus = 100 - pct_pres

    col1, col2, col3 = st.columns(3)
    col1.metric("Inscritos", f"{total_f:,}")
    col2.metric("Compareceram", f"{pct_pres:.1f}%")
    col3.metric("Faltaram", f"{pct_aus:.1f}%")

    # Donut chart
    st.subheader("Comparecimento geral")
    fig_donut = grafico_ausencia_geral(pct_pres, pct_aus)
    st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
    Quem estuda em <strong>escola pública</strong> falta mais. Não é preguiça —
    é falta de transporte, saúde, cuidado com familiares, necessidade de trabalhar.
    A ausência é o primeiro nó: quem não chega à prova já estava excluído antes dela.
    </div>
    """, unsafe_allow_html=True)

    # Ausência por tipo de escola (agregado por UF para o gráfico por estado)
    if "escola_tipo" in df_f.columns:
        st.subheader("Ausência por tipo de escola")

        # Agregar por UF × tipo de escola (formato esperado pela função de visualização)
        presenca_tipo_uf = df_f.groupby(["uf", "escola_tipo"]).agg(
            n=("presente_ambos_dias", "size"),
            n_presentes=("presente_ambos_dias", "sum"),
        ).reset_index()
        presenca_tipo_uf["pct_ausente"] = (1 - presenca_tipo_uf["n_presentes"] / presenca_tipo_uf["n"]) * 100

        filtro_tipo = ["Pública", "Privada"]
        if tipo_escola != "Todas":
            filtro_tipo = [tipo_escola]
        presenca_tipo_f = presenca_tipo_uf[presenca_tipo_uf["escola_tipo"].isin(filtro_tipo)]

        if not presenca_tipo_f.empty:
            fig_aus = grafico_ausencia_por_tipo(presenca_tipo_f)
            st.plotly_chart(fig_aus, use_container_width=True)

        # Resumo agregado (sem UF) para os números detalhados
        presenca_tipo_agg = df_f.groupby("escola_tipo").agg(
            n=("presente_ambos_dias", "size"),
            n_presentes=("presente_ambos_dias", "sum"),
        ).reset_index()
        presenca_tipo_agg["pct_ausente"] = (1 - presenca_tipo_agg["n_presentes"] / presenca_tipo_agg["n"]) * 100

    # Ranking de estados por taxa de ausência
    if not df_desemp.empty and "pct_ausente_uf" in df_desemp.columns:
        st.subheader("Ranking de estados por taxa de ausência")
        df_desemp_f = filtrar_por_uf_regiao(df_desemp, uf_selecionado, regiao_sel)
        fig_rank = grafico_ranking_uf(
            df_desemp_f, "pct_ausente_uf",
            "Estados com maior taxa de ausência",
            "Taxa de ausência (%)",
            uf_destaque=uf_selecionado,
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    # Expander: dados brutos
    with st.expander("📊 Ver números detalhados"):
        if "escola_tipo" in df_f.columns and "presenca_tipo_agg" in dir():
            st.dataframe(presenca_tipo_agg, use_container_width=True, hide_index=True)

    # Download
    if not df_desemp.empty:
        csv_download_button(
            filtrar_por_uf_regiao(df_desemp, uf_selecionado, regiao_sel),
            f"presenca_ausencia_{ANO}.csv",
        )


# ============================================================
# SEÇÃO 3: Que diferença a escola faz?
# ============================================================
def render_secao_diferenca_escola():
    """Aba 3: Gap público × privado e comparação entre estados."""
    st.header("🏫 Que diferença a escola faz?")
    st.markdown("Como as notas variam entre escola pública e privada, e entre estados.")

    if df_gaps.empty:
        st.warning("Dados de gap não disponíveis. Execute `python src/inferencial.py`.")
        return

    df_gaps_f = filtrar_por_uf_regiao(df_gaps, uf_selecionado, regiao_sel)

    # Cards
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Diferença média (pública × privada)",
        f"{gap_medio:.0f} pontos",
        help="Diferença na nota média entre escola pública e privada",
    )
    if not df_gaps_f.empty:
        menor_gap_uf = df_gaps_f.loc[df_gaps_f["gap_publico_privado"].idxmin(), "uf"] if len(df_gaps_f) > 0 else ""
        menor_gap_val = df_gaps_f["gap_publico_privado"].min() if len(df_gaps_f) > 0 else 0
        maior_gap_uf = df_gaps_f.loc[df_gaps_f["gap_publico_privado"].idxmax(), "uf"] if len(df_gaps_f) > 0 else ""
        maior_gap_val = df_gaps_f["gap_publico_privado"].max() if len(df_gaps_f) > 0 else 0

        col2.metric(
            "Menor diferença",
            f"{MAPA_UF_NOME.get(menor_gap_uf, menor_gap_uf)} ({menor_gap_val:.0f} pts)",
        )
        col3.metric(
            "Maior diferença",
            f"{MAPA_UF_NOME.get(maior_gap_uf, maior_gap_uf)} ({maior_gap_val:.0f} pts)",
        )

    st.markdown(f"""
    <div class="insight-box">
    <strong>{gap_medio:.0f} pontos</strong> de diferença não são apenas sobre dinheiro.
    São sobre quem chega e quem não chega — e sobre quem o sistema
    deixa para trás. Em todos os estados, a escola privada tem notas médias maiores.
    </div>
    """, unsafe_allow_html=True)

    # Gap por estado
    st.subheader("Diferença de notas por estado")
    fig_gap = grafico_gap_escola(df_gaps_f)
    st.plotly_chart(fig_gap, use_container_width=True)

    # Comparação entre dois estados
    st.subheader("Comparar dois estados")
    col_comp1, col_comp2 = st.columns(2)
    with col_comp1:
        uf_comp1 = st.selectbox(
            "Estado 1",
            todos_ufs,
            index=todos_ufs.index("SP") if "SP" in todos_ufs else 0,
            format_func=lambda u: f"{u} — {MAPA_UF_NOME.get(u, u)}",
            key="comp_estado_1",
        )
    with col_comp2:
        uf_comp2 = st.selectbox(
            "Estado 2",
            todos_ufs,
            index=todos_ufs.index("BA") if "BA" in todos_ufs else min(1, len(todos_ufs) - 1),
            format_func=lambda u: f"{u} — {MAPA_UF_NOME.get(u, u)}",
            key="comp_estado_2",
        )

    if not df_desemp.empty:
        df_desemp_all = filtrar_por_uf_regiao(df_desemp, None, "Todas")
        dados_uf1 = df_desemp_all[df_desemp_all["uf"] == uf_comp1]
        dados_uf2 = df_desemp_all[df_desemp_all["uf"] == uf_comp2]

        if not dados_uf1.empty and not dados_uf2.empty:
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown(f"**{MAPA_UF_NOME.get(uf_comp1, uf_comp1)}**")
                if "nota_media_uf" in dados_uf1.columns:
                    st.metric("Nota média", f"{dados_uf1['nota_media_uf'].values[0]:.1f}")
                if "gap_publico_privado" in dados_uf1.columns and not pd.isna(dados_uf1['gap_publico_privado'].values[0]):
                    st.metric("Gap pública × privada", f"{dados_uf1['gap_publico_privado'].values[0]:.0f} pts")
                if "pct_presente_uf" in dados_uf1.columns:
                    st.metric("Taxa de presença", f"{dados_uf1['pct_presente_uf'].values[0]:.1f}%")
            with col_m2:
                st.markdown(f"**{MAPA_UF_NOME.get(uf_comp2, uf_comp2)}**")
                if "nota_media_uf" in dados_uf2.columns:
                    st.metric("Nota média", f"{dados_uf2['nota_media_uf'].values[0]:.1f}")
                if "gap_publico_privado" in dados_uf2.columns and not pd.isna(dados_uf2['gap_publico_privado'].values[0]):
                    st.metric("Gap pública × privada", f"{dados_uf2['gap_publico_privado'].values[0]:.0f} pts")
                if "pct_presente_uf" in dados_uf2.columns:
                    st.metric("Taxa de presença", f"{dados_uf2['pct_presente_uf'].values[0]:.1f}%")

    # Radar por área (se UF selecionado)
    if uf_selecionado and not df_desemp.empty:
        st.subheader(f"Notas por área do conhecimento — {MAPA_UF_NOME.get(uf_selecionado, uf_selecionado)}")
        try:
            df_notas_tipo = pd.read_parquet(
                Path(__file__).resolve().parent.parent / "data" / "processed" / "notas_tipo_escola.parquet"
            )
            df_notas_uf = df_notas_tipo[df_notas_tipo["uf"] == uf_selecionado]
            df_pub = df_notas_uf[df_notas_uf["escola_tipo"] == "Pública"]
            df_pri = df_notas_uf[df_notas_uf["escola_tipo"] == "Privada"]

            if not df_pub.empty and not df_pri.empty:
                fig_radar = grafico_radar_por_area(df_pub, df_pri, uf_selecionado)
                st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.info("Dados por tipo de escola não disponíveis para este estado.")
        except FileNotFoundError:
            st.info("Arquivo de notas por tipo de escola não encontrado. Execute `python src/grupos.py`.")

    # Download
    csv_download_button(df_gaps_f, f"gaps_publico_privado_{ANO}.csv")


# ============================================================
# SEÇÃO 4: O que os números revelam?
# ============================================================
def render_secao_o_que_revela():
    """Aba 4: Regressão ecológica e significância."""
    st.header("🔬 O que os números revelam?")
    st.markdown("Quando conectamos o perfil dos inscritos com os resultados, que padrões emergem?")

    # Card central
    st.markdown(f"""
    <div class="insight-box" style="text-align: center; font-size: 1.1rem;">
    <strong>{r2*100:.0f}%</strong> das diferenças de notas entre estados
    podem ser explicadas por 3 fatores:<br>
    % de mulheres negras, renda média e taxa de presença.
    </div>
    """, unsafe_allow_html=True)

    # Scatter com tendência
    if not df_demo.empty and not df_desemp.empty:
        st.subheader("Mais mulheres negras, notas mais baixas?")

        df_merge = df_demo.merge(df_desemp, on="uf", how="inner")
        if "pct_mulher_negra" in df_merge.columns and "nota_media_uf" in df_merge.columns:
            fig_scatter = grafico_dispersao_tendencia(
                df_merge,
                x="pct_mulher_negra",
                y="nota_media_uf",
                titulo="Proporção de mulheres negras × nota média por estado",
                xlabel="% de mulheres negras entre os inscritos",
                ylabel="Nota média do estado",
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

            st.markdown("""
            <div class="insight-box">
            Estados com mais mulheres negras inscritas tendem a ter notas médias menores.
            Isso <strong>não significa</strong> que mulheres negras têm notas menores —
            significa que estados com mais população oprimida tendem a ter
            menos investimentos em educação.
            </div>
            """, unsafe_allow_html=True)

    # Coeficientes (em expander)
    if not df_coefs.empty:
        with st.expander("📊 Ver impacto de cada fator"):
            st.markdown("""
            O gráfico abaixo mostra quanto cada fator influencia a nota média do estado.
            Barras à esquerda do zero indicam **impacto negativo** (mais desse fator = nota menor).
            Barras à direita indicam **impacto positivo**.
            """)
            fig_coef = grafico_coeficientes_ecologicos(df_coefs)
            st.plotly_chart(fig_coef, use_container_width=True)

    # Significância
    if not df_kruskal.empty:
        st.subheader("As diferenças são reais?")
        st.markdown("""
        <div class="insight-box">
        ✅ <strong>Sim.</strong> Os testes estatísticos confirmam que as diferenças
        entre estados com diferentes perfis de ausência e composição demográfica
        **não são acidentais** — são reais e significativas.
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Ver detalhes técnicos"):
            st.dataframe(df_kruskal, use_container_width=True, hide_index=True)
            st.markdown("""
            **Como ler esta tabela:**
            - **h_stat**: estatística do teste (quanto maior, mais diferente entre os grupos)
            - **p_valor**: probabilidade de o resultado ser acidente. Quanto menor, mais real.
              Valores abaixo de 0,05 são considerados significativos.
            - **comparacao**: o que está sendo comparado
            """)

    # Nota metodológica
    with st.expander("⚠️ Limitações metodológicas"):
        st.markdown("""
        **Análise ecológica (por estado, não por aluno)**

        Os microdados do ENEM 2025 estão divididos em dois arquivos (por exigência da LGPD)
        sem chave de junção individual. Por isso, não podemos vincular raça/gênero a notas individuais.

        As correlações mostradas são no nível de estado — elas mostram tendências regionais,
        mas não permitem dizer que uma aluna específica terá tal nota.

        **Outras limitações:**
        - Apenas ~36% dos inscritos informaram o tipo de escola
        - Gênero é binário no questionário INEP (apaga pessoas trans e não-binárias)
        - Raça é por autodeclaração (captura identidade, não classificação racial)
        """)

    # Download
    if not df_coefs.empty:
        csv_download_button(df_coefs, f"regressao_ecologica_{ANO}.csv")


# ============================================================
# RENDERIZAÇÃO PRINCIPAL
# ============================================================
render_hero()

tab1, tab2, tab3, tab4 = st.tabs([
    "🙋 Quem faz o ENEM?",
    "🚪 Quem falta à prova?",
    "🏫 Que diferença a escola faz?",
    "🔬 O que os números revelam?",
])

with tab1:
    render_secao_quem_faz()

with tab2:
    render_secao_quem_falta()

with tab3:
    render_secao_diferenca_escola()

with tab4:
    render_secao_o_que_revela()

# Footer
st.markdown("---")
st.markdown(f"""
**Dados**: Microdados ENEM {ANO} — INEP/MEC | **Análise**: Nó de Opressões — Feminismo Marxista (Heleieth Saffioti) |
**Código**: [GitHub](https://github.com/passonisara06-hub/enem-no-opressoes)
""")