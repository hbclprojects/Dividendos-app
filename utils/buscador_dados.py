"""
Módulo responsável por buscar e processar dados de ações via yfinance.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st


@st.cache_data(ttl=3600)
def buscar_info_basica(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info if info else {}
    except Exception:
        return {}


@st.cache_data(ttl=3600)
def buscar_dividendos_historicos(ticker: str) -> pd.Series:
    try:
        stock = yf.Ticker(ticker)
        divs = stock.dividends
        if divs is None or divs.empty:
            return pd.Series(dtype=float)
        if divs.index.tz is not None:
            divs = divs.copy()
            divs.index = divs.index.tz_localize(None)
        return divs
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=3600)
def buscar_demonstrativo_resultados(ticker: str) -> pd.DataFrame:
    try:
        stock = yf.Ticker(ticker)
        df = stock.income_stmt
        return df if df is not None and not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def buscar_balanco_patrimonial(ticker: str) -> pd.DataFrame:
    try:
        stock = yf.Ticker(ticker)
        df = stock.balance_sheet
        return df if df is not None and not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return f if np.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def calcular_dividendos_anuais(dividends: pd.Series) -> pd.Series:
    """Agrega dividendos por ano excluindo o ano corrente (incompleto)."""
    if dividends is None or dividends.empty:
        return pd.Series(dtype=float)
    try:
        divs = dividends.copy()
        if divs.index.tz is not None:
            divs.index = divs.index.tz_localize(None)
        try:
            annual = divs.resample("YE").sum()
        except Exception:
            annual = divs.resample("A").sum()
        current_year = datetime.now().year
        annual = annual[annual.index.year < current_year]
        annual = annual[annual > 0]
        return annual.sort_index()
    except Exception:
        return pd.Series(dtype=float)


def calcular_anos_consecutivos(annual_divs: pd.Series) -> int:
    """Conta quantos anos consecutivos a empresa aumentou o dividendo anual."""
    if annual_divs is None or len(annual_divs) < 2:
        return 0
    values = annual_divs.sort_index().values
    consecutive = 0
    for i in range(len(values) - 1, 0, -1):
        if values[i] > values[i - 1]:
            consecutive += 1
        else:
            break
    return consecutive


def calcular_cagr(series: pd.Series, anos: int) -> float | None:
    """CAGR para N anos (usa todos disponíveis se menos que N+1 pontos)."""
    if series is None or len(series) < 2:
        return None
    s = series.sort_index()
    if len(s) > anos:
        start, end, n = s.iloc[-(anos + 1)], s.iloc[-1], anos
    else:
        start, end, n = s.iloc[0], s.iloc[-1], len(s) - 1
    if start <= 0 or n <= 0:
        return None
    return (end / start) ** (1.0 / n) - 1


def extrair_eps_historico(financials: pd.DataFrame) -> pd.Series:
    """Extrai série histórica de EPS (diluído preferido) do DRE."""
    if financials is None or financials.empty:
        return pd.Series(dtype=float)
    for key in ["Diluted EPS", "Basic EPS", "Diluted Earnings Per Share", "Basic Earnings Per Share"]:
        if key in financials.index:
            eps = financials.loc[key].dropna()
            if isinstance(eps, pd.Series) and not eps.empty:
                return eps.sort_index()
    return pd.Series(dtype=float)


def extrair_acoes_circulacao(balanco: pd.DataFrame) -> pd.Series:
    """Extrai série histórica de ações em circulação do balanço."""
    if balanco is None or balanco.empty:
        return pd.Series(dtype=float)
    for key in ["Ordinary Shares Number", "Share Issued", "Common Stock"]:
        if key in balanco.index:
            shares = balanco.loc[key].dropna()
            if isinstance(shares, pd.Series) and not shares.empty:
                # Filtra valores que claramente são valor par (muito pequenos)
                if shares.max() > 1_000:
                    return shares.sort_index()
    return pd.Series(dtype=float)


def calcular_tendencia_acoes(shares: pd.Series) -> str:
    if shares is None or len(shares) < 2:
        return "N/D"
    s = shares.sort_index()
    first, last = s.iloc[0], s.iloc[-1]
    if first <= 0:
        return "N/D"
    change = (last - first) / first
    if change < -0.02:
        return "Diminuindo"
    elif change > 0.02:
        return "Aumentando"
    return "Estável"


def calcular_payout_historico(financials: pd.DataFrame, annual_divs: pd.Series) -> pd.Series:
    """Calcula payout ratio histórico combinando EPS e dividendos por ano."""
    eps_hist = extrair_eps_historico(financials)
    if eps_hist.empty or annual_divs.empty:
        return pd.Series(dtype=float)
    result = {}
    for date in eps_hist.index:
        eps_val = _safe_float(eps_hist[date])
        if eps_val is None or eps_val <= 0:
            continue
        year = date.year
        match = annual_divs[annual_divs.index.year == year]
        if not match.empty:
            div_val = match.iloc[0]
            payout = div_val / eps_val
            if 0 < payout <= 2.5:  # cap exibição
                result[date] = payout
    return pd.Series(result, dtype=float).sort_index()


@st.cache_data(ttl=3600)
def buscar_dados_completos(ticker: str) -> dict:
    """Ponto central: retorna dict com todos os dados processados de uma ação."""
    t = ticker.upper().strip()
    result = {
        "ticker": t,
        "nome": None,
        "setor": None,
        "forward_pe": None,
        "dividend_yield": None,
        "payout_ratio": None,
        "preco": None,
        "dividendo_anual_por_acao": None,
        "anos_consecutivos": 0,
        "cagr_dividendos_5a": None,
        "cagr_eps": None,
        "anos_eps_disponivel": 0,
        "tendencia_acoes": "N/D",
        "yield_mais_crescimento": None,
        "ultimo_aumento_div": None,
        "retorno_esperado": None,
        "historico_dividendos_anuais": pd.Series(dtype=float),
        "historico_eps": pd.Series(dtype=float),
        "historico_acoes": pd.Series(dtype=float),
        "historico_payout": pd.Series(dtype=float),
        "erro": None,
    }
    try:
        info = buscar_info_basica(t)
        if not info or info.get("quoteType") is None:
            result["erro"] = f"Ticker '{t}' não encontrado ou sem dados disponíveis."
            return result

        result["nome"] = info.get("longName") or info.get("shortName") or t
        result["setor"] = info.get("sector") or ""
        result["forward_pe"] = _safe_float(info.get("forwardPE"))
        result["preco"] = _safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
        result["dividendo_anual_por_acao"] = _safe_float(info.get("dividendRate"))

        # Dividend yield: yfinance pode retornar como decimal (0.0261) ou percentual (2.61)
        dy_raw = _safe_float(info.get("dividendYield"))
        if dy_raw is not None:
            result["dividend_yield"] = dy_raw / 100 if dy_raw > 0.5 else dy_raw

        # Payout ratio: normalizar igualmente
        pr_raw = _safe_float(info.get("payoutRatio"))
        if pr_raw is not None:
            result["payout_ratio"] = pr_raw / 100 if pr_raw > 2.5 else pr_raw

        # Valida P/E (negativo ou absurdo = sem sentido)
        pe = result["forward_pe"]
        if pe is not None and (pe < 0 or pe > 999):
            result["forward_pe"] = None

        # Valida payout final
        pr = result["payout_ratio"]
        if pr is not None and (pr < 0 or pr > 2.5):
            result["payout_ratio"] = None

        # Dividendos históricos
        divs_raw = buscar_dividendos_historicos(t)
        annual_divs = calcular_dividendos_anuais(divs_raw)
        result["historico_dividendos_anuais"] = annual_divs

        if not annual_divs.empty:
            result["anos_consecutivos"] = calcular_anos_consecutivos(annual_divs)
            result["cagr_dividendos_5a"] = calcular_cagr(annual_divs, 5)
            sorted_a = annual_divs.sort_index()
            if len(sorted_a) >= 2 and sorted_a.iloc[-2] > 0:
                result["ultimo_aumento_div"] = sorted_a.iloc[-1] / sorted_a.iloc[-2] - 1

        # DRE
        financials = buscar_demonstrativo_resultados(t)
        if not financials.empty:
            eps_hist = extrair_eps_historico(financials)
            result["historico_eps"] = eps_hist
            eps_pos = eps_hist[eps_hist > 0] if not eps_hist.empty else eps_hist
            if len(eps_pos) >= 2:
                result["cagr_eps"] = calcular_cagr(eps_pos, 10)
                result["anos_eps_disponivel"] = len(eps_pos) - 1
            result["historico_payout"] = calcular_payout_historico(financials, annual_divs)

        # Balanço
        balanco = buscar_balanco_patrimonial(t)
        if not balanco.empty:
            shares_hist = extrair_acoes_circulacao(balanco)
            result["historico_acoes"] = shares_hist
            result["tendencia_acoes"] = calcular_tendencia_acoes(shares_hist)

        # Métricas derivadas
        dy = result["dividend_yield"]
        cagr_div = result["cagr_dividendos_5a"]
        cagr_eps = result["cagr_eps"]

        if dy is not None and cagr_div is not None:
            result["yield_mais_crescimento"] = dy + cagr_div
        if dy is not None and cagr_eps is not None:
            result["retorno_esperado"] = dy + cagr_eps

    except Exception as e:
        result["erro"] = f"Erro ao processar {t}: {str(e)}"

    return result
