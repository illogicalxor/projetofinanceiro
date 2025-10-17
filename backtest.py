import yfinance as yf
import pandas as pd


def get_stock_data(ticker, start="2000-01-01", end="2025-02-01"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start, end=end, auto_adjust=True)

        if hist.empty:
            print(f"Erro: Não foi possível obter dados para {ticker}")
            return 0, 0, None

        # Remove possíveis preços NaN iniciais e encontra a primeira data válida
        hist = hist.dropna(subset=["Close"])
        first_valid_date = hist.index.min().date() if not hist.empty else None

        # Garante que as colunas necessárias existem
        hist["Dividends"] = hist.get("Dividends", 0)

        df = hist[["Close", "Dividends"]].reset_index()
        df.columns = ["Date", "Close", "Dividends"]

        shares = 0
        monthly_investment = 1000
        total_aportes = 0

        # Seleciona o primeiro dia útil de cada mês para os aportes
        df["Month"] = df["Date"].dt.to_period("M")
        first_days = df.groupby("Month").first()

        for _, row in first_days.iterrows():
            if row["Close"] > 0:
                shares_bought = monthly_investment / row["Close"]
                shares += shares_bought
                total_aportes += monthly_investment

        latest_price = df.iloc[-1]["Close"]
        patrimonio_total = shares * latest_price

        return patrimonio_total, total_aportes, first_valid_date
    except Exception as e:
        print(f"Erro ao processar {ticker}: {e}")
        return 0, 0, None


while True:
    s = 0
    total_investido = 0
    datas_iniciais = {}

    a = input("Digite os tickers (ou 'sair' para encerrar): ").strip()

    if a.lower() == "sair":
        break

    tickers = a.split(" ")

    for ticker in tickers:
        if ticker[-1] in "341":
            ticker += ".SA"

        patrimonio, investido, data_inicial = get_stock_data(ticker)
        s += patrimonio
        total_investido += investido
        datas_iniciais[ticker] = data_inicial

    print(f"Valor total do portfólio: R${s:,.2f}")
    print(f"Valor total investido: R${total_investido:,.2f}")
    for ticker, data in datas_iniciais.items():
        print(f"Primeira data válida para {ticker}: {data}")
