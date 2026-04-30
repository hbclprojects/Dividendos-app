"""
Página 1 – Triagem de Ações
Analisa múltiplos tickers pelos 7 critérios e apresenta tabela comparativa.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.buscador_dados import buscar_dados_completos
from utils.calculos import calcular_pontuacao, fmt_pct

st.set_page_config(page_title="Triagem de Ações", page_icon="📋", layout="wide")

# ── Estilos ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.section-title { font-size:1.5rem; font-weight:700; color:#00d4aa; margin:1rem 0 0.5rem; }
.help-text      { color:#aaa; font-size:0.88rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📋 Triagem de Ações por Dividendos")
st.markdown("Insira os tickers que deseja analisar e aplique os 7 critérios automaticamente.")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Filtros")
    pontuacao_min = st.slider("Pontuação mínima", 0, 100, 50, 5,
                              help="Mostrar apenas ações com pontuação igual ou acima deste valor")
    apenas_aprovados = st.checkbox("Somente aprovados", False)
    st.divider()
    st.markdown('<p class="help-text">Pontuação máxima: 100 pontos.<br>Aprovação: ≥ 60 pts e ≥ 5 critérios atendidos.</p>',
                unsafe_allow_html=True)

# ── Input de Tickers ─────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🔎 Tickers para Análise</div>', unsafe_allow_html=True)

tickers_default = "JNJ, KO, PG, MSFT, ABBV, O, VZ, MMM, ABT, AFL, ADP, T, MCD, WMT"
tickers_input = st.text_area(
    "Digite os tickers separados por vírgula (formato americano):",
    value=tickers_default,
    height=68,
    help="Exemplos: AAPL, JNJ, KO, PG, O, MSFT",
)

col_btn, col_aviso = st.columns([1, 4])
with col_btn:
    analisar = st.button("🔍 Analisar", type="primary", use_container_width=True)
with col_aviso:
    st.markdown('<p class="help-text" style="margin-top:0.6rem;">A primeira busca pode demorar alguns segundos. Resultados são cacheados por 1h.</p>',
                unsafe_allow_html=True)

# ── Processamento ────────────────────────────────────────────────────────────
if analisar:
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
    if not tickers:
        st.error("Insira pelo menos um ticker válido.")
        st.stop()

    resultados = []
    erros = []

    prog = st.progress(0, text="Iniciando busca...")
    for i, tk in enumerate(tickers):
        prog.progress((i + 1) / len(tickers), text=f"Buscando dados de {tk}… ({i+1}/{len(tickers)})")
        dados = buscar_dados_completos(tk)

        if dados.get("erro"):
            erros.append({"ticker": tk, "erro": dados["erro"]})
            continue

        pts, criterios, aprovado = calcular_pontuacao(dados)

        dy    = dados.get("dividend_yield")
        pe    = dados.get("forward_pe")
        cd5   = dados.get("cagr_dividendos_5a")
        pr    = dados.get("payout_ratio")
        anos  = dados.get("anos_consecutivos", 0)
        yc    = dados.get("yield_mais_crescimento")
        ceps  = dados.get("cagr_eps")
        tend  = dados.get("tendencia_acoes", "N/D")

        resultados.append({
            "Ticker":          tk,
            "Nome":            (dados.get("nome") or tk)[:30],
            "Preço":           f"${dados['preco']:.2f}" if dados.get("preco") else "N/D",
            "P/E Forward":     f"{pe:.1f}×" if pe else "N/D",
            "Div. Yield":      fmt_pct(dy),
            "Cresc. Div. 5A":  fmt_pct(cd5, 1),
            "Payout Ratio":    fmt_pct(pr, 1),
            "Anos Consec.":    anos,
            "Yield+Cresc.":    fmt_pct(yc, 1),
            "Cresc. LPA":      fmt_pct(ceps, 1),
            "Tend. Ações":     tend,
            "Pontuação":       pts,
            "Status":          "✅ APROVADO" if aprovado else "❌ REPROVADO",
            # raw para ordenação
            "_pe":    pe or 999,
            "_dy":    dy or 0,
            "_cd5":   cd5 or 0,
            "_pts":   pts,
            "_aprov": aprovado,
        })

    prog.empty()
    st.session_state["triagem_resultado"] = resultados
    st.session_state["triagem_erros"] = erros

# ── Exibição de Resultados ───────────────────────────────────────────────────
if "triagem_resultado" in st.session_state:
    resultados = st.session_state["triagem_resultado"]
    erros      = st.session_state.get("triagem_erros", [])

    if not resultados:
        st.warning("Nenhum resultado disponível. Verifique os tickers inseridos.")
        if erros:
            with st.expander("⚠️ Erros"):
                for e in erros:
                    st.error(f"**{e['ticker']}**: {e['erro']}")
        st.stop()

    df = pd.DataFrame(resultados)

    # Aplica filtros
    df_f = df[df["_pts"] >= pontuacao_min].copy()
    if apenas_aprovados:
        df_f = df_f[df_f["_aprov"] == True]
    df_f = df_f.sort_values("_pts", ascending=False)

    # ── Métricas de resumo ───────────────────────────────────────────────────
    st.markdown('<div class="section-title">📊 Resumo</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    total_a = len(df)
    aprov_a = int(df["_aprov"].sum())
    media_p = df["_pts"].mean()
    melhor  = df.loc[df["_pts"].idxmax(), "Ticker"] if len(df) > 0 else "—"

    c1.metric("Analisadas",       total_a)
    c2.metric("Aprovadas",        aprov_a)
    c3.metric("Reprovadas",       total_a - aprov_a)
    c4.metric("Pontuação Média",  f"{media_p:.1f}")
    c5.metric("Melhor Ação",      melhor)

    st.divider()

    # ── Tabela Principal ─────────────────────────────────────────────────────
    st.markdown(f'<div class="section-title">📋 Resultados ({len(df_f)} ações)</div>', unsafe_allow_html=True)

    cols_vis = ["Ticker", "Nome", "Preço", "P/E Forward", "Div. Yield", "Cresc. Div. 5A",
                "Payout Ratio", "Anos Consec.", "Yield+Cresc.", "Cresc. LPA",
                "Tend. Ações", "Pontuação", "Status"]
    df_vis = df_f[[c for c in cols_vis if c in df_f.columns]].reset_index(drop=True)

    def _cor_status(val):
        if "APROVADO" in str(val):
            return "background-color: rgba(0,200,100,0.15); color:#00c864; font-weight:700"
        return "background-color: rgba(255,60,60,0.12); color:#ff5555; font-weight:700"

    def _cor_pts(val):
        if not isinstance(val, (int, float)):
            return ""
        # Interpola de vermelho (0) → amarelo (50) → verde (100)
        if val >= 70:
            return "background-color: rgba(0,200,100,0.18); color:#00c864; font-weight:700"
        if val >= 50:
            return "background-color: rgba(240,165,0,0.18); color:#f0a500; font-weight:700"
        return "background-color: rgba(255,60,60,0.15); color:#ff5555; font-weight:700"

    styled = (
        df_vis.style
        .applymap(_cor_status, subset=["Status"])
        .applymap(_cor_pts,    subset=["Pontuação"])
    )

    st.dataframe(styled, use_container_width=True, height=min(600, 80 + len(df_vis) * 38))

    # ── Gráfico de Barras – Pontuação ─────────────────────────────────────────
    if len(df_f) > 0:
        st.markdown('<div class="section-title">📊 Pontuação Comparativa</div>', unsafe_allow_html=True)
        df_chart = df_f[["Ticker", "Pontuação", "_aprov"]].copy()
        df_chart["Aprovação"] = df_chart["_aprov"].map({True: "Aprovado", False: "Reprovado"})
        fig = px.bar(
            df_chart.sort_values("Pontuação", ascending=True),
            x="Pontuação", y="Ticker", orientation="h",
            color="Aprovação",
            color_discrete_map={"Aprovado": "#00d4aa", "Reprovado": "#ff5555"},
            title="Pontuação por Ação (0–100 pontos)",
            labels={"Pontuação": "Pontuação Total", "Ticker": "Ticker"},
        )
        fig.add_vline(x=60, line_dash="dash", line_color="#f0a500",
                      annotation_text="Mínimo (60)", annotation_position="top right")
        fig.update_layout(
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
            font_color="#fafafa", showlegend=True,
            height=max(300, len(df_chart) * 32 + 80),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Erros ────────────────────────────────────────────────────────────────
    if erros:
        with st.expander(f"⚠️ {len(erros)} ticker(s) com erro"):
            for e in erros:
                st.error(f"**{e['ticker']}**: {e['erro']}")

    st.divider()
    st.caption("⚠️ Esta ferramenta é apenas para fins educacionais. Você é o único responsável pelas suas decisões de investimento.")
