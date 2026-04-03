"""
Core financial analysis functions.

Consolidates all business logic from the original scattered scripts:
- DCA backtest (monthly contributions)
- Lump sum backtest (single investment)
- Net income in BRL/USD
- Adjusted price charts
- IPCA inflation (BCB API)
- Selic rate (BCB API)
- Bitcoin prices (CoinGecko API)
- Fundamentus scraping
"""

from datetime import datetime, timedelta

import io
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import yfinance as yf


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalise_ticker(ticker: str) -> str:
    """Add .SA suffix to Brazilian tickers when missing."""
    t = ticker.strip().upper()
    if not t:
        raise ValueError("Ticker vazio.")
    if "." in t:
        return t
    if re.match(r"^[A-Z]{4}\d", t):
        return t + ".SA"
    return t


# ---------------------------------------------------------------------------
# Backtest — DCA (aportes mensais)
# ---------------------------------------------------------------------------


def backtest_dca(
    ticker: str,
    monthly_investment: float = 1000,
    start: str = "2000-01-01",
    end: str | None = None,
) -> dict:
    """
    Simula aportes mensais fixos no primeiro dia de negociação de cada mês.

    Usa ``auto_adjust=True`` para que o preço já incorpore dividendos e splits
    (Total Return).

    Returns
    -------
    dict with keys: ticker, patrimonio_final, total_investido, lucro_abs,
                    rentabilidade_pct, data_inicio_real, data_fim
    """
    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")

    ticker = _normalise_ticker(ticker)
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start, end=end, auto_adjust=True)

    if hist.empty:
        raise ValueError(f"Sem dados de preço para {ticker} no período informado.")

    hist.index = hist.index.tz_localize(None)

    df_mensal = hist.resample("MS").first()

    total_shares = 0.0
    total_invested = 0.0

    for _, row in df_mensal.iterrows():
        price = row["Close"]
        if pd.isna(price) or price <= 0:
            continue
        total_shares += monthly_investment / price
        total_invested += monthly_investment

    ultimo_preco = hist["Close"].iloc[-1]
    patrimonio_final = total_shares * ultimo_preco
    lucro_abs = patrimonio_final - total_invested
    rentabilidade = (lucro_abs / total_invested * 100) if total_invested else 0

    return {
        "ticker": ticker,
        "patrimonio_final": patrimonio_final,
        "total_investido": total_invested,
        "lucro_abs": lucro_abs,
        "rentabilidade_pct": rentabilidade,
        "data_inicio_real": hist.index.min().date(),
        "data_fim": hist.index.max().date(),
    }


# ---------------------------------------------------------------------------
# Backtest — Lump Sum (aporte único)
# ---------------------------------------------------------------------------


def backtest_lump_sum(
    ticker: str,
    initial_investment: float = 10000,
    start: str = "2000-01-01",
    end: str | None = None,
) -> dict:
    """
    Simula um único aporte na primeira data disponível e mantém até o fim.

    Usa ``auto_adjust=True`` (Total Return).
    """
    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")

    ticker = _normalise_ticker(ticker)
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start, end=end, auto_adjust=True)

    if hist.empty:
        raise ValueError(f"Sem dados de preço para {ticker} no período informado.")

    hist.index = hist.index.tz_localize(None)

    first_price = hist["Close"].iloc[0]
    shares = initial_investment / first_price
    ultimo_preco = hist["Close"].iloc[-1]
    patrimonio_final = shares * ultimo_preco
    lucro_abs = patrimonio_final - initial_investment
    rentabilidade = (lucro_abs / initial_investment * 100) if initial_investment else 0

    return {
        "ticker": ticker,
        "patrimonio_final": patrimonio_final,
        "total_investido": initial_investment,
        "lucro_abs": lucro_abs,
        "rentabilidade_pct": rentabilidade,
        "data_inicio_real": hist.index.min().date(),
        "data_fim": hist.index.max().date(),
    }


# ---------------------------------------------------------------------------
# Lucro líquido (Net Income) — BRL e USD
# ---------------------------------------------------------------------------


def _fetch_net_income(ticker: str, start: str, end: str) -> pd.Series:
    """Return annual net income filtered by year range."""
    stock = yf.Ticker(ticker)
    df_fin = stock.financials

    if df_fin.empty:
        raise ValueError(f"Dados financeiros indisponíveis para {ticker}.")

    label = "Net Income"
    if label not in df_fin.index:
        alternatives = [l for l in df_fin.index if "Net Income" in l]
        if alternatives:
            label = alternatives[0]
        else:
            raise ValueError(f"Lucro líquido não encontrado para {ticker}.")

    lucro = df_fin.loc[label].sort_index()
    lucro.index = pd.to_datetime(lucro.index).year

    start_year = pd.to_datetime(start).year
    end_year = pd.to_datetime(end).year
    lucro = lucro[(lucro.index >= start_year) & (lucro.index <= end_year)]

    if lucro.empty:
        raise ValueError(
            f"Sem dados de lucro entre {start_year} e {end_year} para {ticker}. "
            "O Yahoo Finance fornece apenas os últimos ~4 anos."
        )
    return lucro


def get_net_income_brl(ticker: str, start: str = "2010-01-01", end: str | None = None) -> pd.Series:
    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")
    ticker = _normalise_ticker(ticker)
    return _fetch_net_income(ticker, start, end)


def get_net_income_usd(ticker: str, start: str = "2010-01-01", end: str | None = None) -> pd.Series:
    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")
    ticker = _normalise_ticker(ticker)
    lucro_brl = _fetch_net_income(ticker, start, end)

    usd = yf.download("USDBRL=X", start=f"{lucro_brl.index.min()}-01-01",
                       end=f"{lucro_brl.index.max()}-12-31", progress=False)
    if isinstance(usd.columns, pd.MultiIndex):
        usd_close = usd["Close"].iloc[:, 0]
    else:
        usd_close = usd["Close"]
    dolar_anual = usd_close.resample("YE").mean()
    dolar_anual.index = dolar_anual.index.year

    df = pd.DataFrame({"Lucro_BRL": lucro_brl, "USD_BRL": dolar_anual}).dropna()
    return df["Lucro_BRL"] / df["USD_BRL"]


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------


def plot_net_income(ticker: str, mode: str = "BRL",
                    start: str = "2010-01-01", end: str | None = None) -> None:
    """Plot net income as a bar chart in BRL or USD."""
    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")
    ticker_norm = _normalise_ticker(ticker)

    if mode == "USD":
        serie = get_net_income_usd(ticker_norm, start, end)
        titulo = f"Lucro Líquido Anual (USD) — {ticker_norm}"
        ylabel = "USD Bilhões"
    else:
        serie = get_net_income_brl(ticker_norm, start, end)
        titulo = f"Lucro Líquido Anual (BRL) — {ticker_norm}"
        ylabel = "R$ Bilhões"

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(serie.index.astype(str), serie.values / 1e9, color="#2c3e50")
    ax.set_title(titulo)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Ano")
    ax.grid(axis="y", linestyle="--", alpha=0.6)

    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, yval,
                f"{yval:.1f}B", va="bottom", ha="center", fontsize=9)

    fig.tight_layout()
    plt.show()


def plot_adjusted_price(ticker: str, start: str = "2000-01-01",
                        end: str | None = None) -> None:
    """Plot adjusted close price with interactive cursor."""
    import mplcursors
    import matplotlib.ticker as mtick

    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")
    ticker = _normalise_ticker(ticker)

    dados = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if dados.empty:
        raise ValueError(f"Sem dados para {ticker}.")

    if isinstance(dados.columns, pd.MultiIndex):
        close = dados["Close"].iloc[:, 0]
    else:
        close = dados["Close"]

    fig, ax = plt.subplots(figsize=(12, 6))
    (line,) = ax.plot(close.index, close.values, linewidth=1)
    ax.set_title(f"{ticker} — Preço Ajustado por Dividendos")
    ax.set_xlabel("Data")
    ax.set_ylabel("Preço")
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("{x:.2f}"))
    ax.grid(True)

    cursor = mplcursors.cursor(line, hover=True)

    @cursor.connect("add")
    def on_add(sel):
        data = close.index[sel.index].strftime("%d/%m/%Y")
        preco = close.iloc[sel.index]
        sel.annotation.set(text=f"Data: {data}\nPreço: {preco:.2f}", fontsize=9)

    plt.show()


# ---------------------------------------------------------------------------
# IPCA — API Banco Central
# ---------------------------------------------------------------------------


def get_ipca_anual(data_inicial: str = "01/01/2000",
                   data_final: str = "31/12/2025") -> pd.DataFrame:
    """
    Fetch IPCA monthly from BCB API and aggregate to annual sums.

    Returns DataFrame with columns: ano, inflacao_acumulada.
    """
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"
    params = {"formato": "json", "dataInicial": data_inicial, "dataFinal": data_final}

    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    if not data:
        raise ValueError("Nenhum dado IPCA retornado pela API.")

    df = pd.DataFrame(data)
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["valor"] = df["valor"].astype(float)
    df["ano"] = df["data"].dt.year

    inflacao_anual = df.groupby("ano")["valor"].sum().reset_index()
    inflacao_anual.columns = ["ano", "inflacao_acumulada"]
    return inflacao_anual


# ---------------------------------------------------------------------------
# Selic — API Banco Central
# ---------------------------------------------------------------------------


def get_selic_rates(start: str = "2000-01-01") -> pd.DataFrame:
    """
    Fetch historical Selic rate from BCB API.

    Returns DataFrame indexed by date with column ``valor`` (monthly rate, decimal).
    """
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1178/dados?formato=json"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    df = pd.DataFrame(data)
    df["data"] = pd.to_datetime(df["data"], dayfirst=True)
    df["valor"] = df["valor"].astype(float) / 100
    df.set_index("data", inplace=True)
    return df[start:]


def simulate_tesouro_selic(start: str = "2000-01-01",
                           monthly_investment: float = 1000) -> dict:
    """
    Simulate monthly contributions to Tesouro Selic.

    Returns dict with ``patrimonio_final``, ``total_aportes``, ``evolucao`` (DataFrame).
    """
    selic_df = get_selic_rates(start).resample("ME").last()

    patrimonio = 0.0
    total_aportes = 0.0
    records = []

    for date, row in selic_df.iterrows():
        rendimento_mensal = (1 + row["valor"]) ** (1 / 12) - 1
        patrimonio = (patrimonio + monthly_investment) * (1 + rendimento_mensal)
        total_aportes += monthly_investment
        records.append({"data": date, "patrimonio": patrimonio})

    evolucao = pd.DataFrame(records)

    return {
        "patrimonio_final": patrimonio,
        "total_aportes": total_aportes,
        "evolucao": evolucao,
    }


def plot_selic_evolucao(start: str = "2000-01-01",
                        monthly_investment: float = 1000) -> None:
    """Simulate Tesouro Selic and plot equity evolution."""
    resultado = simulate_tesouro_selic(start, monthly_investment)
    ev = resultado["evolucao"]

    print(f"Total investido: R${resultado['total_aportes']:,.2f}")
    print(f"Patrimônio final: R${resultado['patrimonio_final']:,.2f}")

    plt.figure(figsize=(10, 5))
    plt.plot(ev["data"], ev["patrimonio"], label="Patrimônio Acumulado", color="blue")
    plt.xlabel("Ano")
    plt.ylabel("Valor (R$)")
    plt.title("Evolução do Patrimônio no Tesouro Selic")
    plt.legend()
    plt.grid()
    plt.show()


# ---------------------------------------------------------------------------
# Bitcoin — CoinGecko API
# ---------------------------------------------------------------------------


def get_bitcoin_prices(days: int = 180) -> pd.DataFrame:
    """
    Fetch Bitcoin daily prices in USD from CoinGecko.

    Returns DataFrame with columns: data, preco_usd.
    """
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)

    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range"
    params = {
        "vs_currency": "usd",
        "from": int(from_date.timestamp()),
        "to": int(to_date.timestamp()),
    }

    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    prices = data.get("prices", [])
    if not prices:
        raise ValueError("Nenhum dado de preço retornado pela CoinGecko.")

    records = []
    for timestamp, price in prices:
        date = datetime.utcfromtimestamp(timestamp / 1000).strftime("%Y-%m-%d")
        records.append({"data": date, "preco_usd": price})

    return pd.DataFrame(records)


def plot_bitcoin(days: int = 180) -> None:
    """Plot Bitcoin price for the last *days*."""
    df = get_bitcoin_prices(days)

    plt.figure(figsize=(10, 5))
    plt.plot(df["data"], df["preco_usd"], label="Preço Bitcoin (USD)", color="blue")
    plt.xlabel("Data")
    plt.ylabel("Preço (USD)")
    plt.title(f"Preço do Bitcoin — últimos {days} dias")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()


# ---------------------------------------------------------------------------
# Fundamentus scraping
# ---------------------------------------------------------------------------


def get_lucro_fundamentus(ticker: str) -> pd.Series | None:
    """
    Scrape annual net income from Fundamentus.

    Returns Series indexed by year, or None on failure.
    """
    t = ticker.replace(".SA", "").strip().upper()
    url = f"https://www.fundamentus.com.br/proventos.php?papel={t}&tipo=2"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()

        tables = pd.read_html(io.StringIO(resp.text), decimal=",", thousands=".")
        if not tables:
            return None

        df = tables[0]
        df.columns = ["Data", "Lucro", "Tipo"]
        df["Data"] = pd.to_datetime(df["Data"], dayfirst=True)
        df["Ano"] = df["Data"].dt.year
        df["Lucro"] = pd.to_numeric(df["Lucro"], errors="coerce")

        return df.groupby("Ano")["Lucro"].sum().sort_index()
    except Exception:
        return None


def plot_lucro_fundamentus(ticker: str) -> None:
    """Plot net income from Fundamentus with green/red bars."""
    dados = get_lucro_fundamentus(ticker)
    if dados is None or dados.empty:
        print(f"Não foi possível obter dados para {ticker.upper()}.")
        return

    valores_bi = dados.values / 1e9
    anos = dados.index.astype(str)
    cores = ["#27ae60" if x > 0 else "#e74c3c" for x in valores_bi]

    plt.figure(figsize=(12, 6))
    bars = plt.bar(anos, valores_bi, color=cores, alpha=0.8)
    plt.title(f"Lucro Líquido Anual — {ticker.upper()}", fontsize=14, fontweight="bold")
    plt.ylabel("R$ (Bilhões)")
    plt.xlabel("Ano")
    plt.xticks(rotation=45)
    plt.grid(axis="y", linestyle="--", alpha=0.3)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval,
                 f"{yval:.2f}B",
                 va="bottom" if yval > 0 else "top",
                 ha="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    plt.show()
