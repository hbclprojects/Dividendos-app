"""
Módulo de cálculos: pontuação por critérios, projeções e métricas financeiras.
"""

import pandas as pd
import numpy as np

SETORES_ALTO_PAYOUT = ["utilities", "real estate", "energy"]


def calcular_pontuacao(dados: dict) -> tuple[int, list[dict], bool]:
    """
    Calcula pontuação 0–100 com base nos 7 critérios do método.
    Retorna: (pontuacao_total, lista_criterios, aprovado_geral)
    """
    setor = (dados.get("setor") or "").lower()
    alto_payout = any(s in setor for s in SETORES_ALTO_PAYOUT)

    criterios = []
    total = 0

    # ── Critério 1: Anos consecutivos de aumento (máx 20 pts) ──────────────
    anos = dados.get("anos_consecutivos") or 0
    if anos >= 25:
        pts, status, aprov = 20, "✅", True
        desc = f"{anos} anos — Dividend Champion"
    elif anos >= 10:
        pts, status, aprov = 15, "✅", True
        desc = f"{anos} anos — Dividend Contender"
    elif anos >= 5:
        pts, status, aprov = 10, "⚠️", True
        desc = f"{anos} anos — mínimo aceitável (ideal ≥ 10)"
    elif anos >= 1:
        pts, status, aprov = 4, "⚠️", False
        desc = f"{anos} ano(s) — histórico curto"
    else:
        pts, status, aprov = 0, "❌", False
        desc = "Sem histórico de aumentos consecutivos"
    total += pts
    criterios.append({
        "criterio": "1. Anos consecutivos de aumento de dividendos",
        "valor": f"{anos} anos",
        "pontos": pts, "max": 20, "aprovado": aprov,
        "status": status, "descricao": desc,
    })

    # ── Critério 2: Crescimento de LPA (máx 15 pts) ────────────────────────
    cagr_eps = dados.get("cagr_eps")
    anos_eps = dados.get("anos_eps_disponivel") or 0
    if cagr_eps is not None:
        if cagr_eps >= 0.10:
            pts, status, aprov = 15, "✅", True
            desc = f"{cagr_eps*100:.1f}%/ano ({anos_eps}a) — crescimento forte"
        elif cagr_eps >= 0.05:
            pts, status, aprov = 10, "✅", True
            desc = f"{cagr_eps*100:.1f}%/ano ({anos_eps}a) — crescimento saudável"
        elif cagr_eps > 0:
            pts, status, aprov = 5, "⚠️", True
            desc = f"{cagr_eps*100:.1f}%/ano ({anos_eps}a) — crescimento baixo"
        else:
            pts, status, aprov = 0, "❌", False
            desc = f"{cagr_eps*100:.1f}%/ano ({anos_eps}a) — crescimento negativo"
        valor_str = f"{cagr_eps*100:.1f}%/ano"
    else:
        pts, status, aprov = 0, "⚠️", False
        desc = "Dados de LPA não disponíveis via yfinance"
        valor_str = "N/D"
    total += pts
    criterios.append({
        "criterio": "2. Crescimento de LPA",
        "valor": valor_str,
        "pontos": pts, "max": 15, "aprovado": aprov,
        "status": status, "descricao": desc,
    })

    # ── Critério 3: Crescimento de dividendos 5A (máx 15 pts) ──────────────
    cagr_div = dados.get("cagr_dividendos_5a")
    if cagr_div is not None:
        if cagr_div >= 0.07:
            pts, status, aprov = 15, "✅", True
            desc = f"{cagr_div*100:.1f}%/ano — excelente"
        elif cagr_div >= 0.05:
            pts, status, aprov = 10, "✅", True
            desc = f"{cagr_div*100:.1f}%/ano — bom (mín. recomendado: 5%)"
        elif cagr_div >= 0.04:
            pts, status, aprov = 7, "⚠️", True
            desc = f"{cagr_div*100:.1f}%/ano — mínimo aceitável (4%)"
        elif cagr_div > 0:
            pts, status, aprov = 2, "⚠️", False
            desc = f"{cagr_div*100:.1f}%/ano — abaixo do mínimo de 4–5%"
        else:
            pts, status, aprov = 0, "❌", False
            desc = f"{cagr_div*100:.1f}%/ano — dividendo em queda"
        valor_str = f"{cagr_div*100:.1f}%/ano"
    else:
        pts, status, aprov = 0, "⚠️", False
        desc = "Dados insuficientes (< 2 anos de dividendos)"
        valor_str = "N/D"
    total += pts
    criterios.append({
        "criterio": "3. Crescimento de Dividendos (5 anos)",
        "valor": valor_str,
        "pontos": pts, "max": 15, "aprovado": aprov,
        "status": status, "descricao": desc,
    })

    # ── Critério 4: Payout Ratio (máx 15 pts) ──────────────────────────────
    payout = dados.get("payout_ratio")
    limite = 0.75 if alto_payout else 0.60
    lim_label = "75%" if alto_payout else "60%"
    if payout is not None and 0 < payout <= 2.0:
        if payout < 0.40:
            pts, status, aprov = 15, "✅", True
            desc = f"{payout*100:.1f}% — muito conservador"
        elif payout < limite:
            pts, status, aprov = 10, "✅", True
            desc = f"{payout*100:.1f}% — dentro do limite de {lim_label}"
        elif payout < 0.85:
            pts, status, aprov = 3, "⚠️", False
            desc = f"{payout*100:.1f}% — acima do limite de {lim_label}"
        else:
            pts, status, aprov = 0, "❌", False
            desc = f"{payout*100:.1f}% — muito alto, risco de corte de dividendos"
        valor_str = f"{payout*100:.1f}%"
    else:
        pts, status, aprov = 0, "⚠️", False
        desc = "Payout ratio não disponível"
        valor_str = "N/D"
    total += pts
    criterios.append({
        "criterio": "4. Payout Ratio",
        "valor": valor_str,
        "pontos": pts, "max": 15, "aprovado": aprov,
        "status": status, "descricao": desc,
    })

    # ── Critério 5: P/E Forward (máx 15 pts) ───────────────────────────────
    pe = dados.get("forward_pe")
    if pe is not None and 0 < pe < 999:
        if pe < 15:
            pts, status, aprov = 15, "✅", True
            desc = f"{pe:.1f}x — valuation muito atraente"
        elif pe < 20:
            pts, status, aprov = 12, "✅", True
            desc = f"{pe:.1f}x — valuation razoável"
        elif pe < 25:
            pts, status, aprov = 8, "✅", True
            desc = f"{pe:.1f}x — valuation aceitável (limite: 25x)"
        elif pe < 33:
            pts, status, aprov = 2, "⚠️", False
            desc = f"{pe:.1f}x — valuation elevado (ideal < 25x)"
        else:
            pts, status, aprov = 0, "❌", False
            desc = f"{pe:.1f}x — valuation excessivo (máximo: 33x)"
        valor_str = f"{pe:.1f}x"
    else:
        pts, status, aprov = 0, "⚠️", False
        desc = "P/E Forward indisponível ou negativo"
        valor_str = "N/D"
    total += pts
    criterios.append({
        "criterio": "5. P/E Forward",
        "valor": valor_str,
        "pontos": pts, "max": 15, "aprovado": aprov,
        "status": status, "descricao": desc,
    })

    # ── Critério 6: Yield + Crescimento Div 5A (máx 10 pts) ────────────────
    yc = dados.get("yield_mais_crescimento")
    if yc is not None:
        if yc >= 0.12:
            pts, status, aprov = 10, "✅", True
            desc = f"{yc*100:.1f}% — excelente (≥ 12%)"
        elif yc >= 0.10:
            pts, status, aprov = 8, "✅", True
            desc = f"{yc*100:.1f}% — bom (meta: ≥ 10%)"
        elif yc >= 0.08:
            pts, status, aprov = 4, "⚠️", False
            desc = f"{yc*100:.1f}% — abaixo do ideal de 10%"
        else:
            pts, status, aprov = 0, "❌", False
            desc = f"{yc*100:.1f}% — insuficiente (< 8%)"
        valor_str = f"{yc*100:.1f}%"
    else:
        pts, status, aprov = 0, "⚠️", False
        desc = "Dados insuficientes para calcular"
        valor_str = "N/D"
    total += pts
    criterios.append({
        "criterio": "6. Yield + Crescimento de Dividendos (5A)",
        "valor": valor_str,
        "pontos": pts, "max": 10, "aprovado": aprov,
        "status": status, "descricao": desc,
    })

    # ── Critério 7: Tendência de Ações em Circulação (máx 10 pts) ──────────
    tendencia = dados.get("tendencia_acoes") or "N/D"
    if tendencia == "Diminuindo":
        pts, status, aprov = 10, "✅", True
        desc = "Ações em circulação diminuindo — buybacks positivos"
    elif tendencia == "Estável":
        pts, status, aprov = 5, "⚠️", True
        desc = "Ações em circulação estáveis — sem diluição relevante"
    elif tendencia == "Aumentando":
        pts, status, aprov = 0, "❌", False
        desc = "Ações em circulação aumentando — diluição dos acionistas"
    else:
        pts, status, aprov = 3, "⚠️", False
        desc = "Dados de ações em circulação indisponíveis"
    total += pts
    criterios.append({
        "criterio": "7. Tendência de Ações em Circulação",
        "valor": tendencia,
        "pontos": pts, "max": 10, "aprovado": aprov,
        "status": status, "descricao": desc,
    })

    aprovados = sum(1 for c in criterios if c["aprovado"])
    aprovado_geral = total >= 60 and aprovados >= 5

    return total, criterios, aprovado_geral


def projetar_renda_mensal(
    renda_mensal_inicial: float,
    contribuicao_mensal: float,
    crescimento_anual: float,
    yield_novos_investimentos: float,
    meses: int = 120,
) -> pd.DataFrame:
    """
    Projeta renda mensal de dividendos ao longo do tempo.

    Fórmula por mês:
      renda_next = renda * (1 + g_mensal + y_mensal) + contribuicao * y_mensal

    onde:
      g_mensal = crescimento orgânico do dividendo
      y_mensal = yield aplicado aos reinvestimentos e novas contribuições
    """
    g_m = (1 + crescimento_anual) ** (1.0 / 12) - 1
    y_m = yield_novos_investimentos / 12

    registros = []
    renda = max(renda_mensal_inicial, 0.0)

    for mes in range(meses + 1):
        registros.append({
            "Mês": mes,
            "Ano": round(mes / 12, 3),
            "Renda Mensal (USD)": round(renda, 2),
        })
        if mes < meses:
            renda = renda * (1 + g_m + y_m) + contribuicao_mensal * y_m

    return pd.DataFrame(registros)


def projetar_independencia_financeira(
    renda_mensal: float,
    despesas_mensais: float,
    renda_dividendos_atual: float,
    yield_esperado: float,
    crescimento_dividendos: float,
    anos_max: int = 50,
) -> tuple[int | None, pd.DataFrame]:
    """
    Calcula quando a renda de dividendos supera as despesas mensais.
    Retorna: (mes_do_cruzamento_ou_None, DataFrame_com_projecao)
    """
    poupanca = max(renda_mensal - despesas_mensais, 0.0)
    g_m = (1 + crescimento_dividendos) ** (1.0 / 12) - 1
    y_m = yield_esperado / 12
    meses_max = anos_max * 12

    registros = []
    renda_div = max(renda_dividendos_atual, 0.0)
    cruzamento = None

    for mes in range(meses_max + 1):
        registros.append({
            "Mês": mes,
            "Ano": round(mes / 12, 2),
            "Renda de Dividendos (USD)": round(renda_div, 2),
            "Despesas (USD)": despesas_mensais,
        })
        if renda_div >= despesas_mensais and cruzamento is None:
            cruzamento = mes
        if mes < meses_max:
            capital_reinvestido = poupanca + renda_div
            renda_div = renda_div * (1 + g_m) + capital_reinvestido * y_m

    return cruzamento, pd.DataFrame(registros)


def calcular_taxa_poupanca(renda: float, despesas: float) -> float:
    if renda <= 0:
        return 0.0
    return max(0.0, min(1.0, (renda - despesas) / renda))


def fmt_moeda(v: float | None) -> str:
    return f"${v:,.2f}" if v is not None else "N/D"


def fmt_pct(v: float | None, casas: int = 2) -> str:
    return f"{v * 100:.{casas}f}%" if v is not None else "N/D"
