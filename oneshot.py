import yfinance as yf
import pandas as pd
import tkinter as tk
from tkinter import ttk, scrolledtext


def calculate_lump_sum(ticker, initial_investment, start, end):
    try:
        # Ajustar ticker brasileiro
        if ticker[-1] in "341":
            ticker = ticker + ".SA"

        stock = yf.Ticker(ticker)

        # Baixar preços
        hist = stock.history(start=start, end=end, auto_adjust=True)
        if hist.empty:
            return f"Erro: Não foi possível obter dados para {ticker}", 0, None

        # Baixar dividendos e splits (corretíssimo para FIIs)
        actions = stock.actions
        dividends = actions["Dividends"]
        splits = actions["Stock Splits"]

        hist = hist[["Close"]].copy()
        hist.index = pd.to_datetime(hist.index)

        # Achar a primeira data negociada >= start
        try:
            first_valid_date = hist.loc[start:].index[0]
        except:
            return f"Erro: Nenhum dado encontrado após {start}", 0, None

        first_price = hist.loc[first_valid_date, "Close"]

        # Compra inicial
        shares = initial_investment / first_price

        # Loop diário
        for date, row in hist.iterrows():
            price = row["Close"]

            # Aplicar splits
        final_price = hist.iloc[-1]["Close"]
        final_value = shares * final_price

        return None, final_value, first_valid_date

    except Exception as e:
        return f"Erro ao processar {ticker}: {e}", 0, None


def run_backtest():
    output_text.delete("1.0", tk.END)

    a = tickers_entry.get().strip()
    initial_investment = float(investment_entry.get() or 1000)
    start_date = start_date_entry.get() or "2000-01-01"
    end_date = end_date_entry.get() or "2025-02-01"

    if not a:
        output_text.insert(tk.END, "Por favor, digite os tickers.")
        return

    tickers = a.split(" ")

    for ticker in tickers:
        error_msg, patrimonio, data_inicial = calculate_lump_sum(
            ticker, initial_investment, start_date, end_date
        )

        if error_msg:
            output_text.insert(tk.END, error_msg + "\n")
        else:
            output_text.insert(tk.END, f"Ticker: {ticker}\n")
            output_text.insert(tk.END, f"Aporte inicial: R${initial_investment:,.2f}\n")
            output_text.insert(tk.END, f"Patrimônio final: R${patrimonio:,.2f}\n")
            output_text.insert(tk.END, f"Primeira data válida: {data_inicial}\n")
            retorno = (patrimonio / initial_investment - 1) * 100
            output_text.insert(tk.END, f"Retorno total: {retorno:.2f}%\n\n")


# Função copiar
def copy_to_clipboard():
    text = output_text.get("1.0", tk.END)
    if text.strip():
        root.clipboard_clear()
        root.clipboard_append(text)


# GUI
root = tk.Tk()
root.title("Backtest - Aporte Único com Reinvestimento de Dividendos")
root.geometry("600x500")

style = ttk.Style(root)
style.theme_use("clam")

main_frame = ttk.Frame(root, padding="10")
main_frame.pack(fill="both", expand=True)

input_frame = ttk.LabelFrame(main_frame, text="Parâmetros", padding="10")
input_frame.pack(fill="x")

# Tickers
tickers_label = ttk.Label(input_frame, text="Tickers:")
tickers_label.grid(row=0, column=0, sticky="w", pady=5)
tickers_entry = ttk.Entry(input_frame, width=40)
tickers_entry.grid(row=0, column=1, sticky="ew", pady=5)

# Aporte inicial
investment_label = ttk.Label(input_frame, text="Aporte inicial (R$):")
investment_label.grid(row=1, column=0, sticky="w", pady=5)
investment_entry = ttk.Entry(input_frame)
investment_entry.grid(row=1, column=1, sticky="ew", pady=5)
investment_entry.insert(0, "10000")

# Data início
start_date_label = ttk.Label(input_frame, text="Data inicial (YYYY-MM-DD):")
start_date_label.grid(row=2, column=0, sticky="w", pady=5)
start_date_entry = ttk.Entry(input_frame)
start_date_entry.grid(row=2, column=1, sticky="ew", pady=5)
start_date_entry.insert(0, "2010-01-01")

# Data fim
end_date_label = ttk.Label(input_frame, text="Data final (YYYY-MM-DD):")
end_date_label.grid(row=3, column=0, sticky="w", pady=5)
end_date_entry = ttk.Entry(input_frame)
end_date_entry.grid(row=3, column=1, sticky="ew", pady=5)
end_date_entry.insert(0, "2025-02-01")

input_frame.columnconfigure(1, weight=1)

run_button = ttk.Button(main_frame, text="Executar", command=run_backtest)
run_button.pack(pady=10)

output_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
output_frame.pack(fill="both", expand=True)

output_text = scrolledtext.ScrolledText(output_frame, width=80, height=20, wrap=tk.WORD)
output_text.pack(fill="both", expand=True)

copy_button = ttk.Button(output_frame, text="Copiar", command=copy_to_clipboard)
copy_button.pack(pady=5)

root.mainloop()
