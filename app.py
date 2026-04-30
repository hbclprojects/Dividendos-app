"""
Analisador de Crescimento de Dividendos
Página principal / Home
"""

import streamlit as st

st.set_page_config(
    page_title="Analisador de Dividendos",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    color: #00d4aa;
    margin-bottom: 0.3rem;
    line-height: 1.2;
}
.hero-sub {
    font-size: 1.15rem;
    color: #aaa;
    margin-bottom: 2rem;
}
.card {
    background: #16213e;
    border: 1px solid #1f3460;
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    height: 100%;
}
.card h3 { color: #00d4aa; margin-top: 0; }
.disclaimer {
    background: #1a2744;
    border-left: 4px solid #f0a500;
    border-radius: 8px;
    padding: 1rem 1.4rem;
    margin-top: 2rem;
    font-size: 0.95rem;
}
.nav-card {
    background: #16213e;
    border: 1px solid #1f3460;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    transition: border-color 0.2s;
}
.nav-card:hover { border-color: #00d4aa; }
.badge-green  { background:#003d2b; color:#00d4aa; border-radius:6px; padding:2px 8px; font-size:0.82rem; }
.badge-yellow { background:#3d2e00; color:#f0a500; border-radius:6px; padding:2px 8px; font-size:0.82rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-title">💰 Analisador de Crescimento de Dividendos</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Metodologia de investimento focada em renda passiva crescente — meta: US$ 1.000/mês em dividendos</div>', unsafe_allow_html=True)

col_esq, col_dir = st.columns([3, 2], gap="large")

with col_esq:
    st.markdown("""
    <div class="card">
    <h3>📐 A Metodologia</h3>
    <p>Este aplicativo replica a estratégia de um <strong>Dividend Growth Investor</strong>:
    investir ~$1.000/mês em ações de qualidade que pagam e aumentam dividendos consistentemente,
    com o objetivo de gerar <strong>$1.000/mês em renda passiva</strong>.</p>
    <h4 style="color:#f0a500;">Os 7 Critérios de Seleção</h4>
    <table style="width:100%; font-size:0.92rem;">
    <tr><td>✅</td><td><strong>Anos consecutivos</strong> de aumento de dividendos (quanto mais, melhor)</td></tr>
    <tr><td>📈</td><td><strong>Crescimento de LPA</strong> positivo e consistente nos últimos anos</td></tr>
    <tr><td>💰</td><td><strong>Crescimento de dividendos</strong> ≥ 4–5% ao ano (últimos 5 anos)</td></tr>
    <tr><td>📉</td><td><strong>Payout ratio</strong> abaixo de 60% (75% para utilities/REITs)</td></tr>
    <tr><td>💵</td><td><strong>P/E Forward</strong> abaixo de 25× (nunca acima de 33×)</td></tr>
    <tr><td>🎯</td><td><strong>Yield + Crescimento 5A</strong> próximo ou acima de 10%</td></tr>
    <tr><td>📊</td><td><strong>Ações em circulação</strong> com tendência de queda (buybacks)</td></tr>
    </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
    <h3>🧮 Fórmula de Retorno Esperado</h3>
    <p style="font-size:1.1rem; text-align:center; background:#0e1117; padding:0.8rem; border-radius:8px;">
    <strong>Retorno Esperado = Dividend Yield + Crescimento de LPA ± Variação do Múltiplo</strong>
    </p>
    <p><em>Exemplo:</em> Uma ação com Yield de <strong>3%</strong> e crescimento de LPA de <strong>8%/ano</strong>
    com múltiplo estável → Retorno esperado ≈ <strong>11%/ano</strong>, além de uma renda crescente.</p>
    </div>
    """, unsafe_allow_html=True)

with col_dir:
    st.markdown("""
    <div class="card">
    <h3>🗺️ Páginas do Aplicativo</h3>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="nav-card">
    <strong>📋 Triagem de Ações</strong><br>
    <small>Analise múltiplos tickers pelos 7 critérios e veja pontuação comparativa</small>
    </div>
    <div class="nav-card">
    <strong>🔍 Análise Individual</strong><br>
    <small>Gráficos históricos de dividendos, LPA, payout e ações em circulação</small>
    </div>
    <div class="nav-card">
    <strong>💼 Portfólio e Projeção</strong><br>
    <small>Gerencie sua carteira e veja projeção de renda para 10 anos</small>
    </div>
    <div class="nav-card">
    <strong>🧮 Calculadora de Independência</strong><br>
    <small>Calcule em quantos anos sua renda de dividendos supera suas despesas</small>
    </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="card">
    <h3 style="font-size:1rem;">⚡ Dados em tempo real</h3>
    <p style="font-size:0.88rem; color:#aaa;">
    Todos os dados são obtidos via <strong>yfinance</strong> diretamente das bolsas americanas.
    O cache expira a cada <strong>1 hora</strong> para evitar chamadas repetidas.
    Tickers devem estar no formato americano (ex: AAPL, JNJ, KO).
    </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer">
⚠️ <strong>Aviso Importante:</strong> Esta ferramenta é exclusivamente para fins educacionais e não
constitui recomendação de investimento. Investimentos em renda variável envolvem riscos, incluindo
a perda total do capital investido. <strong>Você é o único responsável pelas suas decisões de investimento.</strong>
Consulte um assessor de investimentos certificado antes de tomar qualquer decisão financeira.
</div>
""", unsafe_allow_html=True)
