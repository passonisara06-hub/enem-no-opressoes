"""
dashboard.py — Dashboard narrativo Streamlit (nível agregado)
============================================================
O nó de opressões no ENEM 2025: raça, gênero e classe
como sistema articulado de dominação-exploração
(Heleieth Saffioti, 2004; 2013)

NOTA METODOLÓGICA: A partir de 2020, o INEP dividiu os microdados em
PARTICIPANTES e RESULTADOS sem chave de junção individual (LGPD).
A análise é agregada por UF — correlações ecológicas não implicam
relações individuais.

Rodar:
    streamlit run app/dashboard.py
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

# Adicionar src/ ao path para importar módulos
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from constants import (
    ANO, GRUPOS_PRINCIPAIS, ORDEM_GRUPOS, CORES,
    ARQUIVO_PART_LIMPO, ARQUIVO_RES_LIMPO,
    ARQUIVO_METRICAS_DEMO, ARQUIVO_METRICAS_DESEMP,
    ARQUIVO_REGRESSAO_ECO, ARQUIVO_GAPS_REGIONAIS, ARQUIVO_TESTES_KRUSKAL,
    NOTAS_TODAS,
)
from visualizacoes import (
    grafico_composicao_demografica,
    grafico_notas_por_tipo_escola,
    grafico_ausencia_por_tipo,
    heatmap_composicao_uf,
    grafico_coeficientes_ecologicos,
    grafico_gap_escola,
)

# ------------------------------------------------------------
# Configuração da página
# ------------------------------------------------------------
st.set_page_config(
    page_title=f"ENEM {ANO} — Nó de Opressões",
    page_icon="✊",
    layout="wide",
)

# CSS narrativo
st.markdown("""
<style>
.narrativo {
    background: linear-gradient(135deg, #FFF8E7 0%, #F5DEB3 100%);
    padding: 1.5rem;
    border-radius: 0.5rem;
    border-left: 4px solid #8B4513;
    margin: 1rem 0;
    font-size: 0.95rem;
    line-height: 1.6;
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
    font-size: 0.85rem;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# Carregar dados
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
        st.warning(f"Métricas demográficas não encontradas. Execute `python src/grupos.py`.")

    try:
        dados["metricas_desemp"] = pd.read_parquet(ARQUIVO_METRICAS_DESEMP)
    except FileNotFoundError:
        st.warning(f"Métricas de desempenho não encontradas. Execute `python src/grupos.py`.")

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

# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
st.sidebar.header("Filtros")

# Filtro de UF
todos_ufs = sorted(dados["participantes"]["uf"].unique())
uf_sel = st.sidebar.multiselect("UF", todos_ufs, default=todos_ufs)

# Filtro de tipo de escola
escola_sel = st.sidebar.selectbox("Tipo de escola", ["Todos", "Pública", "Privada"])

# Referências teóricas
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Referências teóricas**

- Saffioti, H. (2004). *O nó do nó de opressões*
- Saffioti, H. (2013). *Gênero, patriarcado, violência*

**Nota metodológica**

Os microdados de 2025 estão divididos em PARTICIPANTES e RESULTADOS
sem chave de junção individual (LGPD). A análise é agregada por UF.
""")

# ------------------------------------------------------------
# Título
# ------------------------------------------------------------
st.title(f"ENEM {ANO} — Nó de Opressões")
st.markdown("""
<div class="narrativo">
<em>O nó de opressões</em> é um conceito de Heleieth Saffioti que articula
raça, gênero e classe como dimensões mutuamente constitutivas de um
<em>sistema articulado de dominação-exploração</em> — não como eixos
independentes que se interceptam, mas como <em>posições estruturais</em>
que se determinam reciprocamente.
</div>

<div class="alerta-metodo">
⚠️ <strong>Nota metodológica:</strong> Por exigência da LGPD, os microdados
de 2025 não permitem vincular dados demográficos (raça, gênero) a notas
individuais. A análise compara <strong>composição demográfica regional</strong>
com <strong>desempenho regional</strong> (análise ecológica). Correlações
agregadas não implicam relações individuais.
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# Seção 1: Quem se inscreve? Composição demográfica
# ------------------------------------------------------------
st.header("1. Quem se inscreve? — Composição demográfica por UF")

if "metricas_demo" in dados and dados["metricas_demo"] is not None:
    df_demo = dados["metricas_demo"]
    if uf_sel:
        df_demo = df_demo[df_demo["uf"].isin(uf_sel)]

    fig_comp = grafico_composicao_demografica(df_demo)
    st.plotly_chart(fig_comp, use_container_width=True)

    fig_heat = heatmap_composicao_uf(df_demo)
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("""
    <div class="narrativo">
    A composição demográfica dos inscritos revela a <em>estrutura social
    desigual</em> que antecede o exame: onde a população negra é maioria,
    os recursos educacionais tendem a ser mais escassos. O nó de opressões
    se manifesta já na possibilidade de se inscrever.
    </div>
    """, unsafe_allow_html=True)
else:
    st.warning("Métricas demográficas não disponíveis. Execute o pipeline completo.")

# ------------------------------------------------------------
# Seção 2: Quem consegue chegar? Ausência por tipo de escola
# ------------------------------------------------------------
st.header("2. Quem consegue chegar? — Ausência e presença")

if "resultados" in dados:
    df_res = dados["resultados"]
    if uf_sel:
        df_res = df_res[df_res["uf"].isin(uf_sel)]

    # Presença geral
    total = len(df_res)
    presentes = df_res["presente_ambos_dias"].sum()
    pct_presente = presentes / total * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de inscritos", f"{total:,}")
    col2.metric("Presentes ambos os dias", f"{presentes:,}")
    col3.metric("Taxa de presença", f"{pct_presente:.1f}%")

    # Presença por tipo de escola
    presenca_tipo = df_res.groupby("escola_tipo").agg(
        n=("presente_ambos_dias", "size"),
        n_presentes=("presente_ambos_dias", "sum"),
    ).reset_index()
    presenca_tipo["pct_ausente"] = (1 - presenca_tipo["n_presentes"] / presenca_tipo["n"]) * 100

    if escola_sel != "Todos":
        presenca_tipo = presenca_tipo[presenca_tipo["escola_tipo"] == escola_sel]

    fig_aus = grafico_ausencia_por_tipo(presenca_tipo)
    st.plotly_chart(fig_aus, use_container_width=True)

    st.markdown("""
    <div class="narrativo">
    A ausência ao exame é um <em>indicador estrutural</em>: quem não chega
    à prova já estava excluído antes dela. Escolas públicas concentram a
    maior taxa de ausência — resultado da <em>interação de opressões</em>
    que vai além da renda individual.
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------
# Seção 3: Desempenho por tipo de escola e UF
# ------------------------------------------------------------
st.header("3. Desempenho — Notas por tipo de escola e UF")

if "metricas_desemp" in dados and dados["metricas_desemp"] is not None:
    df_desemp = dados["metricas_desemp"]
    if uf_sel:
        df_desemp = df_desemp[df_desemp["uf"].isin(uf_sel)]

    area_sel = st.selectbox(
        "Área de conhecimento",
        ["Nota média geral"] + [n.replace("NU_NOTA_", "") for n in NOTAS_TODAS if n != "NU_NOTA_REDACAO"] + ["Redação"],
    )

    # Gap entre público e privado
    if "gap_publico_privado" in df_desemp.columns:
        gap_medio = df_desemp["gap_publico_privado"].mean()
        st.metric("Gap médio Público vs Privado", f"{gap_medio:.1f} pontos")

    fig_gap = grafico_gap_escola(df_desemp.dropna(subset=["gap_publico_privado"]))
    st.plotly_chart(fig_gap, use_container_width=True)

    st.markdown("""
    <div class="narrativo">
    O gap entre escola pública e privada <em>não é apenas de recursos</em>:
    é um gap estrutural que se reproduz porque a escola pública atende
    majoritariamente a população oprimida pelo nó. A desigualdade
    educacional é <em>expressão</em> do nó, não sua causa.
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------
# Seção 4: Análise ecológica
# ------------------------------------------------------------
st.header("4. Análise ecológica — Composição demográfica e desempenho")

if "coefs" in dados and dados["coefs"] is not None and not dados["coefs"].empty:
    coefs = dados["coefs"]
    fig_coef = grafico_coeficientes_ecologicos(coefs)
    st.plotly_chart(fig_coef, use_container_width=True)

    st.markdown("""
    <div class="narrativo">
    A regressão ecológica estima a associação entre <em>composição demográfica
    regional</em> e <em>desempenho médio regional</em>. UFs com maior
    proporção de mulheres negras tendem a ter notas médias menores —
    <em>não porque mulheres negras individualmente têm notas menores</em>,
    mas porque a concentração de população oprimida indica regiões com
    menores investimentos educacionais.
    </div>
    <div class="alerta-metodo">
    ⚠️ Efeito ecológico: estas correlações são no nível de UF,
    não individual. Ver Saffioti (2004) para a articulação teórica.
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Resultados da regressão ecológica não disponíveis. Execute `python src/inferencial.py`.")

# ------------------------------------------------------------
# Seção 5: Testes de significância
# ------------------------------------------------------------
st.header("5. Testes de significância (nível agregado)")

if "kruskal" in dados and dados["kruskal"] is not None and not dados["kruskal"].empty:
    kruskal_df = dados["kruskal"]
    st.dataframe(kruskal_df, use_container_width=True)

    st.markdown("""
    <div class="narrativo">
    Os testes de Kruskal-Wallis comparam a distribuição de notas médias
    entre grupos de UFs com diferentes perfis de ausência e composição
    demográfica. Resultados significativos indicam que a <em>posição
    estrutural regional</em> está associada a diferenças mensuráveis
    no desempenho educacional.
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Testes de Kruskal-Wallis não disponíveis. Execute `python src/inferencial.py`.")

# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------
st.markdown("---")
st.markdown(f"""
**Dados**: Microdados ENEM {ANO} — INEP/MEC
**Análise**: Nó de Opressões — Feminismo Marxista (Heleieth Saffioti)
**Código**: [github.com/seu-usuario/enem-no-opressoes]()

⚠️ **Limitação metodológica**: Os microdados de 2025 estão divididos em
PARTICIPANTES e RESULTADOS sem chave de junção individual (LGPD).
A análise é ecológica (nível UF), não individual.
""")