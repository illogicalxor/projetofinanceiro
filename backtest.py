import yfinance as yf
import pandas as pd
import tkinter as tk
from tkinter import scrolledtext

def get_stock_data(ticker, start="2000-01-01", end="2025-02-01"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(start=start, end=end, auto_adjust=False)  # Get raw data

        if hist.empty:
            return f"Erro: Não foi possível obter dados para {ticker}", 0, 0, None

        hist = hist.dropna(subset=["Close"])
        first_valid_date = hist.index.min().date() if not hist.empty else None

        df = hist[["Close", "Dividends", "Stock Splits"]].reset_index()
        df.columns = ["Date", "Close", "Dividends", "Stock Splits"]

        shares = 0
        monthly_investment = 1000
        total_aportes = 0

        # Get the first trading day of each month
        df['Month'] = df['Date'].dt.to_period('M')
        investment_days = df.groupby('Month')['Date'].first()
        investment_days_set = set(investment_days)

        for _, row in df.iterrows():
            # Adjust shares on split
            if row['Stock Splits'] > 0:
                shares *= row['Stock Splits']

            # Reinvest dividends
            if row['Dividends'] > 0 and shares > 0:
                if row["Close"] > 0:
                    shares += (row['Dividends'] * shares) / row['Close']

            # Monthly investment
            if row['Date'] in investment_days_set:
                if row["Close"] > 0:
                    shares += monthly_investment / row['Close']
                    total_aportes += monthly_investment

        latest_price = df.iloc[-1]["Close"]
        patrimonio_total = shares * latest_price

        return None, patrimonio_total, total_aportes, first_valid_date
    except Exception as e:
        return f"Erro ao processar {ticker}: {e}", 0, 0, None

def run_backtest():
    output_text.delete('1.0', tk.END)
    s = 0
    total_investido = 0
    datas_iniciais = {}

    a = tickers_entry.get().strip()

    if not a:
        output_text.insert(tk.END, "Por favor, digite os tickers.")
        return

    tickers = a.split(" ")

    for ticker in tickers:
        if ticker[-1] in "341":
            ticker += ".SA"

        error_msg, patrimonio, investido, data_inicial = get_stock_data(ticker)
        if error_msg:
            output_text.insert(tk.END, error_msg + "\n")
        else:
            s += patrimonio
            total_investido += investido
            datas_iniciais[ticker] = data_inicial

    output_text.insert(tk.END, f"Valor total do portfólio: R${s:,.2f}\n")
    output_text.insert(tk.END, f"Valor total investido: R${total_investido:,.2f}\n")
    for ticker, data in datas_iniciais.items():
        output_text.insert(tk.END, f"Primeira data válida para {ticker}: {data}\n")


# GUI setup
root = tk.Tk()
root.title("Backtest de Aportes Mensais")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

tickers_label = tk.Label(frame, text="Tickers (separados por espaço):")
tickers_label.pack(side=tk.LEFT)

tickers_entry = tk.Entry(frame, width=50)
tickers_entry.pack(side=tk.LEFT, padx=5)

run_button = tk.Button(frame, text="Executar Backtest", command=run_backtest)
run_button.pack(side=tk.LEFT, padx=5)

output_text = scrolledtext.ScrolledText(root, width=80, height=20)
output_text.pack(padx=10, pady=10)

root.mainloop()