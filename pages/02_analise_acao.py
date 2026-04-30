"""
Página 2 – Análise Individual de Ação
Gráficos históricos e veredicto detalhado por critério.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.buscador_dados import buscar_dados_completos
from utils.calculos import calcular_pontuacao, fmt_pct, fmt_moeda

st.set_page_config(page_title="Análise Individual", page_icon="🔍", layout="wide")

LAYOUT_BASE = dict(
    plot_bgcolor="#0e1117",
    paper_bgcolor="#0e1117",
    font_color="#fafafa",
    xaxis=dict(gridcolor="#1f3460"),
    yaxis=dict(gridcolor="#1f3460"),
)

# ── Estilos ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-label  { font-size:0.82rem; color:#aaa; }
.metric-value  { font-size:1.3rem; font-weight:700; color:#fafafa; }
.metric-box    { background:#16213e; border:1px solid #1f3460; border-radius:10px;
                 padding:0.9rem 1rem; text-align:center; }
.verdict-aprov { background:rgba(0,200,100,0.12); border:1px solid #00c864;
                 border-radius:10px; padding:1rem 1.4rem; color:#00c864;
                 font-size:1.5rem; font-weight:800; text-align:center; }
.verdict-reprov{ background:rgba(255,60,60,0.1); border:1px solid #ff5555;
                 border-radius:10px; padding:1rem 1.4rem; color:#ff5555;
                 font-size:1.5rem; font-weight:800; text-align:center; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🔍 Análise Individual de Ação")
st.markdown("Visualize o histórico e o veredicto detalhado de qualquer ação americana.")

# ── Input ─────────────────────────────────────────────────────────────────────
col_in, col_btn, _ = st.columns([2, 1, 4])
with col_in:
    ticker_input = st.text_input("Ticker da ação:", value="JNJ", max_chars=10,
                                  placeholder="Ex: AAPL, KO, JNJ").upper().strip()
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    buscar = st.button("🔍 Analisar", type="primary")

if not buscar and "analise_ticker" not in st.session_state:
    st.info("Digite um ticker e clique em **Analisar** para começar.")
    st.stop()

if buscar and ticker_input:
    st.session_state["analise_ticker"] = ticker_input

tk = st.session_state.get("analise_ticker", ticker_input)

with st.spinner(f"Buscando dados de {tk}…"):
    dados = buscar_dados_completos(tk)

if dados.get("erro"):
    st.error(f"❌ {dados['erro']}")
    st.stop()

pts, criterios, aprovado = calcular_pontuacao(dados)

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
nome   = dados.get("nome") or tk
setor  = dados.get("setor") or "—"
preco  = dados.get("preco")
st.markdown(f"## {tk} — {nome}")
st.markdown(f"**Setor:** {setor}  |  **Preço atual:** {fmt_moeda(preco)}")
st.divider()

# ── Veredicto ─────────────────────────────────────────────────────────────────
vdict_class = "verdict-aprov" if aprovado else "verdict-reprov"
vdict_text  = "✅ APROVADO" if aprovado else "❌ REPROVADO"
st.markdown(f'<div class="{vdict_class}">{vdict_text} — Pontuação: {pts}/100</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Métricas principais ───────────────────────────────────────────────────────
dy      = dados.get("dividend_yield")
pe      = dados.get("forward_pe")
cd5     = dados.get("cagr_dividendos_5a")
ceps    = dados.get("cagr_eps")
pr      = dados.get("payout_ratio")
anos_c  = dados.get("anos_consecutivos", 0)
ult_inc = dados.get("ultimo_aumento_div")
ret_esp = dados.get("retorno_esperado")
yc      = dados.get("yield_mais_crescimento")

def _metric(label, valor):
    return f"""
    <div class="metric-box">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{valor}</div>
    </div>"""

cols = st.columns(4)
metricas = [
    ("Dividend Yield Atual",       fmt_pct(dy)),
    ("P/E Forward",                f"{pe:.1f}×" if pe else "N/D"),
    ("Cresc. Div. 5A (CAGR)",      fmt_pct(cd5, 1)),
    ("Cresc. LPA (CAGR)",          fmt_pct(ceps, 1)),
    ("Payout Ratio",               fmt_pct(pr, 1)),
    ("Anos Consec. Aumento",       f"{anos_c} anos"),
    ("Último Aumento Div.",        fmt_pct(ult_inc, 1) if ult_inc else "N/D"),
    ("Retorno Esperado (Yield+LPA)", fmt_pct(ret_esp, 1)),
]
for i, (label, val) in enumerate(metricas):
    cols[i % 4].markdown(_metric(label, val), unsafe_allow_html=True)
    if i % 4 == 3 and i < len(metricas) - 1:
        cols = st.columns(4)

st.divider()

# ── Gráficos Históricos ───────────────────────────────────────────────────────
st.markdown("## 📈 Histórico Financeiro")

hist_div  = dados.get("historico_dividendos_anuais", pd.Series(dtype=float))
hist_eps  = dados.get("historico_eps", pd.Series(dtype=float))
hist_acs  = dados.get("historico_acoes", pd.Series(dtype=float))
hist_pr   = dados.get("historico_payout", pd.Series(dtype=float))

col_g1, col_g2 = st.columns(2)

# Gráfico 1 – Dividendos por ação
with col_g1:
    if not hist_div.empty:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=[str(d.year) for d in hist_div.index],
            y=hist_div.values,
            marker_color="#00d4aa",
            name="Dividendos/Ação (Anual)",
        ))
        fig1.update_layout(
            **LAYOUT_BASE,
            title="💰 Dividendos Por Ação (Anual)",
            xaxis_title="Ano", yaxis_title="USD",
            showlegend=False,
        )
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("Dados históricos de dividendos não disponíveis.")

# Gráfico 2 – LPA
with col_g2:
    if not hist_eps.empty:
        eps_df = hist_eps.reset_index()
        eps_df.columns = ["Data", "LPA"]
        eps_df["Ano"] = eps_df["Data"].apply(lambda d: str(d.year) if hasattr(d, 'year') else str(d)[:4])
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=eps_df["Ano"], y=eps_df["LPA"],
            marker_color=[("#00d4aa" if v > 0 else "#ff5555") for v in eps_df["LPA"]],
            name="LPA (Diluído)",
        ))
        fig2.update_layout(
            **LAYOUT_BASE,
            title="📈 Lucro Por Ação — LPA (Diluído)",
            xaxis_title="Ano do Exercício", yaxis_title="USD",
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Dados históricos de LPA não disponíveis (yfinance limita a ~4 anos).")

col_g3, col_g4 = st.columns(2)

# Gráfico 3 – Payout Ratio
with col_g3:
    if not hist_pr.empty:
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=[str(d.year) for d in hist_pr.index],
            y=hist_pr.values * 100,
            mode="lines+markers",
            line=dict(color="#f0a500", width=2),
            marker=dict(size=8),
            name="Payout Ratio",
        ))
        fig3.add_hline(y=60, line_dash="dash", line_color="#ff5555",
                       annotation_text="Limite 60%", annotation_position="top right")
        fig3.add_hline(y=75, line_dash="dot", line_color="#ff8800",
                       annotation_text="Limite 75% (util./REIT)", annotation_position="bottom right")
        fig3.update_layout(
            **LAYOUT_BASE,
            title="📉 Payout Ratio Histórico",
            xaxis_title="Ano", yaxis_title="%",
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Dados de payout histórico insuficientes.")

# Gráfico 4 – Ações em circulação
with col_g4:
    if not hist_acs.empty and len(hist_acs) >= 2:
        acs_vals = hist_acs.values / 1e6  # em milhões
        acs_anos = [str(d.year) if hasattr(d, 'year') else str(d)[:4] for d in hist_acs.index]
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=acs_anos, y=acs_vals,
            mode="lines+markers",
            line=dict(color="#9b59b6", width=2),
            marker=dict(size=8),
            fill="tozeroy", fillcolor="rgba(155,89,182,0.1)",
            name="Ações em Circulação",
        ))
        fig4.update_layout(
            **LAYOUT_BASE,
            title="📊 Ações em Circulação (milhões)",
            xaxis_title="Ano", yaxis_title="Milhões de Ações",
            showlegend=False,
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("Dados de ações em circulação não disponíveis.")

st.divider()

# ── Veredicto por Critério ────────────────────────────────────────────────────
st.markdown("## 📋 Veredicto por Critério")

for c in criterios:
    aprov_c = c["aprovado"]
    bg = "rgba(0,200,100,0.08)" if aprov_c else "rgba(255,60,60,0.06)"
    brd = "#00c864" if aprov_c else "#ff5555"
    pts_text = f"{c['pontos']}/{c['max']} pts"
    st.markdown(f"""
    <div style="background:{bg}; border-left:4px solid {brd}; border-radius:8px;
                padding:0.75rem 1.2rem; margin-bottom:0.5rem;">
      <strong>{c['status']} {c['criterio']}</strong>
      &nbsp;&nbsp;<span style="color:#aaa; font-size:0.88rem;">{pts_text}</span>
      &nbsp;|&nbsp;<code style="color:#ccc;">{c['valor']}</code>
      <br><small style="color:#bbb;">{c['descricao']}</small>
    </div>
    """, unsafe_allow_html=True)

# ── Radar de critérios ────────────────────────────────────────────────────────
st.divider()
st.markdown("## 🕸️ Radar de Pontuação por Critério")

categorias = [c["criterio"].split(". ", 1)[1] if ". " in c["criterio"] else c["criterio"] for c in criterios]
valores    = [c["pontos"] for c in criterios]
maximos    = [c["max"] for c in criterios]
pct_vals   = [v / m * 100 for v, m in zip(valores, maximos)]

fig_r = go.Figure()
fig_r.add_trace(go.Scatterpolar(
    r=pct_vals + [pct_vals[0]],
    theta=categorias + [categorias[0]],
    fill="toself",
    fillcolor="rgba(0,212,170,0.15)",
    line=dict(color="#00d4aa", width=2),
    name=tk,
))
fig_r.update_layout(
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 100], gridcolor="#1f3460"),
        angularaxis=dict(gridcolor="#1f3460"),
        bgcolor="#0e1117",
    ),
    plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
    font_color="#fafafa",
    showlegend=False,
    title=f"Radar de Pontuação — {tk} ({pts}/100 pts)",
)
st.plotly_chart(fig_r, use_container_width=True)

st.caption("⚠️ Esta ferramenta é apenas para fins educacionais. Você é o único responsável pelas suas decisões de investimento.")
