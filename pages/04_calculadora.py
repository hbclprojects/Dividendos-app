"""
Página 4 – Calculadora de Taxa de Poupança e Independência por Dividendos
Baseada na matemática simples por trás da aposentadoria antecipada.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from utils.calculos import (
    projetar_independencia_financeira,
    calcular_taxa_poupanca,
    fmt_moeda,
    fmt_pct,
)

st.set_page_config(page_title="Calculadora de Independência", page_icon="🧮", layout="wide")

LAYOUT_BASE = dict(
    plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
    font_color="#fafafa",
    xaxis=dict(gridcolor="#1f3460"),
    yaxis=dict(gridcolor="#1f3460"),
)

st.markdown("""
<style>
.big-metric  { font-size:2rem; font-weight:800; color:#00d4aa; }
.label-gray  { font-size:0.85rem; color:#aaa; }
.result-card { background:#16213e; border:1px solid #1f3460; border-radius:12px;
               padding:1.2rem 1.5rem; margin-bottom:0.8rem; }
.highlight   { color:#f0a500; font-weight:700; }
.section-title { font-size:1.4rem; font-weight:700; color:#00d4aa; margin:1.2rem 0 0.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🧮 Calculadora de Independência Financeira por Dividendos")
st.markdown(
    "Baseada na matemática da aposentadoria antecipada: **quando sua renda de dividendos superar "
    "suas despesas mensais, você atingiu a independência financeira.**"
)

# ── Inputs ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📥 Seus Dados Atuais</div>', unsafe_allow_html=True)

col_a, col_b = st.columns(2, gap="large")

with col_a:
    st.markdown("**💵 Renda e Despesas**")
    renda_mensal = st.number_input(
        "Renda líquida mensal (USD)", min_value=0.0, value=5000.0, step=100.0,
        help="Sua renda mensal total após impostos",
    )
    despesas_mensais = st.number_input(
        "Despesas mensais totais (USD)", min_value=0.0, value=3500.0, step=100.0,
        help="Seus gastos mensais totais (moradia, alimentação, transporte, etc.)",
    )
    st.markdown("**📊 Situação Atual**")
    portfolio_atual = st.number_input(
        "Valor atual do portfólio (USD)", min_value=0.0, value=50_000.0, step=1_000.0,
        help="Valor total atual da sua carteira de investimentos",
    )
    renda_div_atual = st.number_input(
        "Renda mensal atual de dividendos (USD)", min_value=0.0, value=120.0, step=10.0,
        help="Dividendos que você já recebe por mês hoje",
    )

with col_b:
    st.markdown("**📈 Premissas de Crescimento**")
    yield_esperado_pct = st.slider(
        "Dividend yield esperado em novos investimentos (%)", 0.5, 10.0, 3.0, 0.25,
        help="Yield médio das ações que você pretende comprar",
    )
    cresc_div_pct = st.slider(
        "Taxa anual de crescimento de dividendos (%)", 1.0, 20.0, 7.0, 0.5,
        help="CAGR esperado dos dividendos do portfólio (histórico de boas ações: 6–10%/ano)",
    )
    st.markdown("**🎯 Horizonte de Análise**")
    anos_max = st.slider("Anos máximos de simulação", 10, 50, 40, 5)

calcular = st.button("🧮 Calcular Independência", type="primary", use_container_width=False)

# ── Cálculo Imediato de Taxa de Poupança ──────────────────────────────────────
poupanca_mensal = max(renda_mensal - despesas_mensais, 0.0)
taxa_poupanca   = calcular_taxa_poupanca(renda_mensal, despesas_mensais)

st.divider()
st.markdown('<div class="section-title">📊 Situação Atual</div>', unsafe_allow_html=True)

mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("Poupança Mensal",  fmt_moeda(poupanca_mensal))
mc2.metric("Taxa de Poupança", fmt_pct(taxa_poupanca))
mc3.metric("Renda de Div./Mês", fmt_moeda(renda_div_atual))
mc4.metric("Cobertura Atual",
           f"{(renda_div_atual / despesas_mensais * 100):.1f}%" if despesas_mensais > 0 else "N/D",
           help="% das despesas cobertas pelos dividendos hoje")

if poupanca_mensal <= 0:
    st.error("⚠️ Suas despesas são maiores ou iguais à sua renda. Reduza os gastos para liberar capital para investimentos.")
    st.stop()

# ── Gauge de Progresso ────────────────────────────────────────────────────────
cobertura_atual = min(renda_div_atual / despesas_mensais, 1.0) if despesas_mensais > 0 else 0.0

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=cobertura_atual * 100,
    title={"text": "Cobertura de Despesas pelos Dividendos (%)", "font": {"color": "#fafafa"}},
    delta={"reference": 100, "increasing": {"color": "#00d4aa"}},
    gauge={
        "axis": {"range": [0, 100], "tickcolor": "#fafafa"},
        "bar": {"color": "#00d4aa"},
        "bgcolor": "#16213e",
        "bordercolor": "#1f3460",
        "steps": [
            {"range": [0, 25],   "color": "rgba(255,60,60,0.2)"},
            {"range": [25, 50],  "color": "rgba(240,165,0,0.15)"},
            {"range": [50, 75],  "color": "rgba(240,165,0,0.1)"},
            {"range": [75, 100], "color": "rgba(0,212,170,0.1)"},
        ],
        "threshold": {"line": {"color": "#f0a500", "width": 3}, "value": 100},
    },
    number={"suffix": "%", "font": {"color": "#00d4aa", "size": 36}},
))
fig_gauge.update_layout(
    paper_bgcolor="#0e1117", font_color="#fafafa",
    height=280, margin=dict(t=60, b=20),
)
st.plotly_chart(fig_gauge, use_container_width=True)

# ── Projeção ──────────────────────────────────────────────────────────────────
if calcular or "calc_resultado" in st.session_state:
    if calcular:
        mes_cruzamento, df_proj = projetar_independencia_financeira(
            renda_mensal         = renda_mensal,
            despesas_mensais     = despesas_mensais,
            renda_dividendos_atual = renda_div_atual,
            yield_esperado       = yield_esperado_pct / 100,
            crescimento_dividendos = cresc_div_pct / 100,
            anos_max             = anos_max,
        )
        st.session_state["calc_resultado"] = (mes_cruzamento, df_proj)
        st.session_state["calc_params"] = {
            "renda": renda_mensal, "despesas": despesas_mensais,
            "yield": yield_esperado_pct, "cresc": cresc_div_pct,
        }

    mes_cruzamento, df_proj = st.session_state["calc_resultado"]

    st.divider()
    st.markdown('<div class="section-title">🚀 Projeção de Independência Financeira</div>', unsafe_allow_html=True)

    # ── Resultado Principal ───────────────────────────────────────────────────
    if mes_cruzamento is not None:
        anos_c = mes_cruzamento // 12
        meses_c = mes_cruzamento % 12
        st.markdown(f"""
        <div class="result-card">
          <div class="label-gray">Você atingirá a independência financeira por dividendos em:</div>
          <div class="big-metric">{anos_c} anos e {meses_c} meses</div>
          <div class="label-gray">Ou seja, seus dividendos cobrirão suas despesas de
          <span class="highlight">{fmt_moeda(despesas_mensais)}/mês</span>
          aproximadamente em <span class="highlight">{anos_c} anos</span>.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        renda_final = df_proj["Renda de Dividendos (USD)"].iloc[-1]
        st.warning(
            f"Com as premissas atuais, em {anos_max} anos sua renda de dividendos chegará a "
            f"**{fmt_moeda(renda_final)}/mês**, mas não cobrirá suas despesas de "
            f"**{fmt_moeda(despesas_mensais)}/mês**. Considere aumentar a taxa de poupança, "
            f"o yield alvo ou a taxa de crescimento esperada."
        )

    # ── Gráfico Principal ─────────────────────────────────────────────────────
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_proj["Ano"], y=df_proj["Renda de Dividendos (USD)"],
        name="Renda de Dividendos",
        mode="lines",
        line=dict(color="#00d4aa", width=3),
        fill="tozeroy", fillcolor="rgba(0,212,170,0.07)",
    ))
    fig.add_trace(go.Scatter(
        x=df_proj["Ano"], y=df_proj["Despesas (USD)"],
        name="Despesas Mensais",
        mode="lines",
        line=dict(color="#ff5555", width=2, dash="dash"),
    ))

    if mes_cruzamento is not None:
        ano_crz = mes_cruzamento / 12
        renda_crz = df_proj[df_proj["Mês"] == mes_cruzamento]["Renda de Dividendos (USD)"].iloc[0]
        fig.add_vline(x=ano_crz, line_dash="dash", line_color="#f0a500", line_width=1.5)
        fig.add_trace(go.Scatter(
            x=[ano_crz], y=[renda_crz],
            mode="markers+text",
            marker=dict(color="#f0a500", size=14, symbol="star"),
            text=[f"  Cruzamento: ano {ano_crz:.1f}"],
            textposition="top right",
            textfont=dict(color="#f0a500"),
            name="Ponto de Cruzamento",
            showlegend=True,
        ))

    fig.update_layout(
        **LAYOUT_BASE,
        title="Renda de Dividendos × Despesas ao Longo do Tempo",
        xaxis_title="Anos a partir de hoje",
        yaxis_title="USD / mês",
        legend=dict(bgcolor="#16213e", bordercolor="#1f3460"),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Resumo em Marcos ──────────────────────────────────────────────────────
    st.markdown('<div class="section-title">📌 Marcos da Jornada</div>', unsafe_allow_html=True)

    marcos = [0.25, 0.50, 0.75, 1.00]
    cols_m = st.columns(len(marcos))
    for col, pct in zip(cols_m, marcos):
        alvo = despesas_mensais * pct
        rows = df_proj[df_proj["Renda de Dividendos (USD)"] >= alvo]
        if not rows.empty:
            ano_m = rows["Ano"].iloc[0]
            texto = f"~{ano_m:.1f} anos"
        else:
            texto = f"> {anos_max} anos"
        col.metric(f"{pct*100:.0f}% das despesas cobertas", texto)

    # ── Tabela por Ano ────────────────────────────────────────────────────────
    with st.expander("📋 Ver tabela detalhada por ano"):
        df_anual = df_proj[df_proj["Mês"] % 12 == 0].copy()
        df_anual["Cobertura (%)"] = (df_anual["Renda de Dividendos (USD)"] / despesas_mensais * 100).round(1)
        df_anual = df_anual[["Ano", "Renda de Dividendos (USD)", "Despesas (USD)", "Cobertura (%)"]].reset_index(drop=True)
        st.dataframe(
            df_anual.style.format({
                "Renda de Dividendos (USD)": "${:,.2f}",
                "Despesas (USD)":            "${:,.2f}",
                "Cobertura (%)":             "{:.1f}%",
            }).background_gradient(subset=["Cobertura (%)"], cmap="RdYlGn", vmin=0, vmax=100),
            use_container_width=True,
        )

st.divider()

# ── Explicação da Matemática ──────────────────────────────────────────────────
with st.expander("📚 A matemática por trás dos cálculos"):
    st.markdown("""
    ### A Matemática Simples da Independência por Dividendos

    O modelo de projeção funciona assim, para cada mês:

    ```
    1. A renda de dividendos existente cresce organicamente pela taxa de crescimento de dividendos
    2. Você reinveste toda a poupança (renda - despesas) + os dividendos recebidos
    3. O capital reinvestido gera nova renda de dividendos ao yield esperado
    4. O processo se compõe mês a mês até os dividendos >= despesas
    ```

    **Fórmula mensal:**

    ```
    renda_próximo_mês = renda_atual × (1 + g_mensal)
                        + (poupança + renda_atual) × yield_mensal
    ```

    onde:
    - `g_mensal = (1 + taxa_crescimento_anual)^(1/12) - 1`
    - `yield_mensal = yield_anual / 12`

    **Variáveis que mais impactam:**
    - 💪 **Taxa de poupança alta** acelera muito o processo
    - 📈 **Crescimento de dividendos** mantém o poder de compra da renda
    - 🔄 **Reinvestimento dos dividendos** cria o efeito de juros compostos
    """)

st.caption("⚠️ Esta ferramenta é apenas para fins educacionais. Projeções são estimativas baseadas em premissas simplificadas. O desempenho passado não garante resultados futuros. Você é o único responsável pelas suas decisões de investimento.")
