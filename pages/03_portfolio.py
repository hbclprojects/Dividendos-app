"""
Página 3 – Portfólio e Projeção de Renda
Gerenciamento de carteira e projeção de renda de dividendos para 10 anos.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.calculos import projetar_renda_mensal, fmt_moeda

st.set_page_config(page_title="Portfólio e Projeção", page_icon="💼", layout="wide")

META_MENSAL = 1_000.0

st.markdown("""
<style>
.metric-box { background:#16213e; border:1px solid #1f3460; border-radius:10px;
              padding:0.9rem 1rem; text-align:center; }
.metric-label { font-size:0.82rem; color:#aaa; }
.metric-value { font-size:1.35rem; font-weight:700; }
.section-title { font-size:1.4rem; font-weight:700; color:#00d4aa; margin:1.2rem 0 0.5rem; }
</style>
""", unsafe_allow_html=True)

LAYOUT_BASE = dict(
    plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
    font_color="#fafafa",
    xaxis=dict(gridcolor="#1f3460"),
    yaxis=dict(gridcolor="#1f3460"),
)

st.markdown("# 💼 Portfólio e Projeção de Renda")
st.markdown("Cadastre suas posições e visualize a trajetória até a meta de **$1.000/mês** em dividendos.")

# ── Tabela de Portfólio ───────────────────────────────────────────────────────
st.markdown('<div class="section-title">📊 Suas Posições</div>', unsafe_allow_html=True)
st.markdown("Edite a tabela abaixo diretamente. **Dividendo Anual/Ação** = dividendo anual por ação (USD).")

portfolio_inicial = pd.DataFrame({
    "Ticker":              ["JNJ",  "KO",   "PG",   "ABBV", "O"],
    "Ações":               [10,     20,     8,      15,     25],
    "Custo/Ação (USD)":    [155.0,  60.0,   145.0,  175.0,  55.0],
    "Div. Anual/Ação (USD)": [4.76, 1.94,   3.76,   5.92,   3.12],
})

portfolio_df = st.data_editor(
    portfolio_inicial,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Ticker":              st.column_config.TextColumn("Ticker", width="small"),
        "Ações":               st.column_config.NumberColumn("Nº de Ações", min_value=0, step=1),
        "Custo/Ação (USD)":    st.column_config.NumberColumn("Custo/Ação (USD)", min_value=0.0, format="%.2f"),
        "Div. Anual/Ação (USD)": st.column_config.NumberColumn("Div. Anual/Ação (USD)", min_value=0.0, format="%.4f"),
    },
    key="portfolio_editor",
)

# ── Parâmetros de Projeção ────────────────────────────────────────────────────
st.markdown('<div class="section-title">⚙️ Parâmetros de Projeção</div>', unsafe_allow_html=True)

p_col1, p_col2, p_col3 = st.columns(3)
with p_col1:
    contrib_mensal = st.number_input(
        "Investimento mensal (USD)", min_value=0.0, value=1000.0, step=100.0,
        help="Valor que você pretende investir todo mês em novas ações",
    )
with p_col2:
    cresc_div_pct = st.slider(
        "Taxa anual de crescimento de dividendos (%)", 0.0, 20.0, 6.0, 0.5,
        help="CAGR esperado dos dividendos do portfólio. Use os resultados da Triagem como referência.",
    )
with p_col3:
    yield_novos_pct = st.slider(
        "Yield médio em novos investimentos (%)", 0.5, 10.0, 3.0, 0.25,
        help="Dividend yield estimado das novas ações que você comprará com as contribuições mensais.",
    )

calcular = st.button("📈 Calcular Projeção", type="primary")

# ── Cálculos do Portfólio ─────────────────────────────────────────────────────
df_port = portfolio_df.dropna(subset=["Ticker", "Ações", "Custo/Ação (USD)", "Div. Anual/Ação (USD)"])
df_port = df_port[df_port["Ações"] > 0]

if df_port.empty:
    st.warning("Adicione ao menos uma posição válida na tabela acima.")
    st.stop()

df_port = df_port.copy()
df_port["Valor Posição (USD)"] = df_port["Ações"] * df_port["Custo/Ação (USD)"]
df_port["Renda Anual (USD)"]   = df_port["Ações"] * df_port["Div. Anual/Ação (USD)"]
df_port["Renda Mensal (USD)"]  = df_port["Renda Anual (USD)"] / 12
df_port["Div. Yield (%)"]      = (df_port["Div. Anual/Ação (USD)"] / df_port["Custo/Ação (USD)"] * 100).round(2)

total_valor        = df_port["Valor Posição (USD)"].sum()
total_renda_anual  = df_port["Renda Anual (USD)"].sum()
total_renda_mensal = total_renda_anual / 12
progresso          = min(total_renda_mensal / META_MENSAL, 1.0)

# ── Métricas do Portfólio ─────────────────────────────────────────────────────
st.markdown('<div class="section-title">💰 Renda Atual do Portfólio</div>', unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)

def _mbox(label, val, cor="#fafafa"):
    return f'<div class="metric-box"><div class="metric-label">{label}</div><div class="metric-value" style="color:{cor};">{val}</div></div>'

m1.markdown(_mbox("Valor Total do Portfólio", fmt_moeda(total_valor)), unsafe_allow_html=True)
m2.markdown(_mbox("Renda Anual de Dividendos", fmt_moeda(total_renda_anual), "#00d4aa"), unsafe_allow_html=True)
m3.markdown(_mbox("Renda Mensal de Dividendos", fmt_moeda(total_renda_mensal), "#00d4aa"), unsafe_allow_html=True)
m4.markdown(_mbox("Meta Mensal", fmt_moeda(META_MENSAL), "#f0a500"), unsafe_allow_html=True)
m5.markdown(_mbox("Progresso para a Meta", f"{progresso*100:.1f}%", "#00d4aa" if progresso >= 1 else "#f0a500"),
            unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("**Progresso em direção à meta de $1.000/mês:**")
st.progress(progresso)
if progresso >= 1.0:
    st.success(f"🎉 Parabéns! Você atingiu sua meta de ${META_MENSAL:,.0f}/mês em renda de dividendos!")
else:
    faltam = META_MENSAL - total_renda_mensal
    st.info(f"Faltam **{fmt_moeda(faltam)}/mês** para atingir a meta de ${META_MENSAL:,.0f}/mês.")

st.divider()

# ── Tabela detalhada do portfólio ─────────────────────────────────────────────
with st.expander("📋 Ver detalhes do portfólio"):
    cols_show = ["Ticker", "Ações", "Custo/Ação (USD)", "Valor Posição (USD)",
                 "Div. Anual/Ação (USD)", "Div. Yield (%)", "Renda Anual (USD)", "Renda Mensal (USD)"]
    cols_show = [c for c in cols_show if c in df_port.columns]
    st.dataframe(
        df_port[cols_show].style.format({
            "Custo/Ação (USD)":      "${:,.2f}",
            "Valor Posição (USD)":   "${:,.2f}",
            "Div. Anual/Ação (USD)": "${:,.4f}",
            "Div. Yield (%)":        "{:.2f}%",
            "Renda Anual (USD)":     "${:,.2f}",
            "Renda Mensal (USD)":    "${:,.2f}",
        }),
        use_container_width=True,
    )

# ── Gráficos de Alocação ──────────────────────────────────────────────────────
st.markdown('<div class="section-title">🥧 Alocação do Portfólio</div>', unsafe_allow_html=True)

gc1, gc2 = st.columns(2)

with gc1:
    fig_pie1 = px.pie(
        df_port, values="Valor Posição (USD)", names="Ticker",
        title="Alocação por Valor da Posição",
        color_discrete_sequence=px.colors.qualitative.Bold,
        hole=0.4,
    )
    fig_pie1.update_layout(paper_bgcolor="#0e1117", font_color="#fafafa",
                            legend=dict(bgcolor="#16213e"))
    st.plotly_chart(fig_pie1, use_container_width=True)

with gc2:
    fig_pie2 = px.pie(
        df_port, values="Renda Anual (USD)", names="Ticker",
        title="Alocação por Renda Anual de Dividendos",
        color_discrete_sequence=px.colors.qualitative.Bold,
        hole=0.4,
    )
    fig_pie2.update_layout(paper_bgcolor="#0e1117", font_color="#fafafa",
                            legend=dict(bgcolor="#16213e"))
    st.plotly_chart(fig_pie2, use_container_width=True)

st.divider()

# ── Projeção de Renda ─────────────────────────────────────────────────────────
if calcular or "proj_calculada" in st.session_state:
    if calcular:
        proj = projetar_renda_mensal(
            renda_mensal_inicial    = total_renda_mensal,
            contribuicao_mensal     = contrib_mensal,
            crescimento_anual       = cresc_div_pct / 100,
            yield_novos_investimentos = yield_novos_pct / 100,
            meses                   = 120,
        )
        st.session_state["proj_calculada"] = proj
        st.session_state["proj_params"] = {
            "contrib": contrib_mensal,
            "cresc": cresc_div_pct,
            "yield": yield_novos_pct,
        }

    proj = st.session_state["proj_calculada"]
    params = st.session_state.get("proj_params", {})

    st.markdown('<div class="section-title">📈 Projeção de Renda — 10 Anos</div>', unsafe_allow_html=True)
    st.markdown(f"**Premissas:** contribuição de {fmt_moeda(params.get('contrib', contrib_mensal))}/mês · "
                f"crescimento de dividendos de {params.get('cresc', cresc_div_pct):.1f}%/ano · "
                f"yield em novos investimentos de {params.get('yield', yield_novos_pct):.2f}%/ano")

    # Encontrar mês em que bate $1.000
    acima_meta = proj[proj["Renda Mensal (USD)"] >= META_MENSAL]
    mes_meta = int(acima_meta["Mês"].iloc[0]) if not acima_meta.empty else None

    # Gráfico
    fig_proj = go.Figure()
    fig_proj.add_trace(go.Scatter(
        x=proj["Ano"], y=proj["Renda Mensal (USD)"],
        mode="lines",
        name="Renda Mensal Projetada",
        line=dict(color="#00d4aa", width=3),
        fill="tozeroy", fillcolor="rgba(0,212,170,0.08)",
    ))
    fig_proj.add_hline(y=META_MENSAL, line_dash="dash", line_color="#f0a500", line_width=2,
                       annotation_text=f"Meta: ${META_MENSAL:,.0f}/mês",
                       annotation_position="top left")
    fig_proj.add_hline(y=total_renda_mensal, line_dash="dot", line_color="#888",
                       annotation_text=f"Hoje: {fmt_moeda(total_renda_mensal)}/mês",
                       annotation_position="bottom right")

    if mes_meta is not None:
        ano_meta = mes_meta / 12
        renda_meta = proj[proj["Mês"] == mes_meta]["Renda Mensal (USD)"].iloc[0]
        fig_proj.add_vline(x=ano_meta, line_dash="dash", line_color="#f0a500", line_width=1.5)
        fig_proj.add_trace(go.Scatter(
            x=[ano_meta], y=[renda_meta],
            mode="markers",
            marker=dict(color="#f0a500", size=12, symbol="star"),
            name=f"Meta atingida em {ano_meta:.1f} anos",
            showlegend=True,
        ))

    fig_proj.update_layout(
        **LAYOUT_BASE,
        title="Projeção de Renda Mensal de Dividendos (próximos 10 anos)",
        xaxis_title="Anos a partir de hoje",
        yaxis_title="Renda Mensal (USD)",
        legend=dict(bgcolor="#16213e", bordercolor="#1f3460"),
        hovermode="x unified",
    )
    st.plotly_chart(fig_proj, use_container_width=True)

    # Tabela resumo por ano
    with st.expander("📋 Ver tabela de projeção anual"):
        proj_anual = proj[proj["Mês"] % 12 == 0].copy()
        proj_anual["Renda Anual (USD)"] = proj_anual["Renda Mensal (USD)"] * 12
        proj_anual["Ano"] = proj_anual["Mês"] // 12
        st.dataframe(
            proj_anual[["Ano", "Renda Mensal (USD)", "Renda Anual (USD)"]].style.format({
                "Renda Mensal (USD)": "${:,.2f}",
                "Renda Anual (USD)":  "${:,.2f}",
            }),
            use_container_width=True,
        )

    if mes_meta is not None:
        anos_meta = mes_meta // 12
        meses_meta = mes_meta % 12
        renda_final = proj["Renda Mensal (USD)"].iloc[-1]
        st.success(f"🎯 Com estas premissas, você atingirá **${META_MENSAL:,.0f}/mês** em aproximadamente "
                   f"**{anos_meta} anos e {meses_meta} meses**.")
        st.metric("Renda mensal estimada em 10 anos", fmt_moeda(renda_final))
    else:
        renda_final = proj["Renda Mensal (USD)"].iloc[-1]
        st.warning(f"Com as premissas atuais, a renda em 10 anos será de **{fmt_moeda(renda_final)}/mês**, "
                   f"abaixo da meta de ${META_MENSAL:,.0f}/mês. Considere aumentar a contribuição mensal "
                   f"ou o yield alvo.")

st.divider()
st.caption("⚠️ Esta ferramenta é apenas para fins educacionais. Projeções são estimativas baseadas em premissas simplificadas e não garantem resultados futuros. Você é o único responsável pelas suas decisões de investimento.")
