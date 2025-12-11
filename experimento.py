import yfinance as yf
import pandas as pd
import tkinter as tk
from tkinter import ttk, scrolledtext


def get_stock_data(ticker, monthly_investment, start, end):
    try:
        stock = yf.Ticker(ticker)

        # Preço ajustado = total return series (splits + dividendos)
        hist = stock.history(start=start, end=end, auto_adjust=True)

        if hist.empty:
            return f"Erro: Não foi possível obter dados para {ticker}", 0, 0, None

        hist = hist.dropna(subset=["Close"])
        first_valid_date = hist.index.min().date()

        df = hist[["Close"]].reset_index()
        df.columns = ["Date", "Close"]

        # Obter 1º dia de negociação de cada mês
        df["Month"] = df["Date"].dt.to_period("M")
        investment_days = df.groupby("Month")["Date"].first()
        investment_days_set = set(investment_days)

        shares = 0
        total_aportes = 0

        for _, row in df.iterrows():
            if row["Date"] in investment_days_set:
                if row["Close"] > 0:
                    shares += monthly_investment / row["Close"]
                    total_aportes += monthly_investment

        latest_price = df.iloc[-1]["Close"]
        patrimonio_total = shares * latest_price

        return None, patrimonio_total, total_aportes, first_valid_date

    except Exception as e:
        return f"Erro ao processar {ticker}: {e}", 0, 0, None


def run_backtest():
    output_text.delete("1.0", tk.END)
    s = 0
    total_investido = 0
    datas_iniciais = {}

    a = tickers_entry.get().strip()
    monthly_investment = float(investment_entry.get() or 1000)
    start_date = start_date_entry.get() or "2000-01-01"
    end_date = end_date_entry.get() or "2025-02-01"

    if not a:
        output_text.insert(tk.END, "Por favor, digite os tickers.")
        return

    tickers = a.split(" ")

    for ticker in tickers:
        if ticker[-1] in "341":
            ticker += ".SA"

        error_msg, patrimonio, investido, data_inicial = get_stock_data(
            ticker, monthly_investment, start_date, end_date
        )
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


def copy_to_clipboard():
    text = output_text.get("1.0", tk.END)
    if text.strip():
        root.clipboard_clear()
        root.clipboard_append(text)


# GUI setup
root = tk.Tk()
root.title("Backtest de Aportes Mensais")
root.geometry("600x500")

style = ttk.Style(root)
style.theme_use("clam")

main_frame = ttk.Frame(root, padding="10")
main_frame.pack(fill="both", expand=True)

input_frame = ttk.LabelFrame(main_frame, text="Parâmetros do Backtest", padding="10")
input_frame.pack(fill="x")

ttk.Label(input_frame, text="Tickers (separados por espaço):").grid(
    row=0, column=0, sticky="w", padx=5, pady=5
)
tickers_entry = ttk.Entry(input_frame, width=40)
tickers_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

ttk.Label(input_frame, text="Valor do Aporte Mensal:").grid(
    row=1, column=0, sticky="w", padx=5, pady=5
)
investment_entry = ttk.Entry(input_frame)
investment_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
investment_entry.insert(0, "1000")

ttk.Label(input_frame, text="Data de Início (YYYY-MM-DD):").grid(
    row=2, column=0, sticky="w", padx=5, pady=5
)
start_date_entry = ttk.Entry(input_frame)
start_date_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
start_date_entry.insert(0, "2000-01-01")

ttk.Label(input_frame, text="Data de Fim (YYYY-MM-DD):").grid(
    row=3, column=0, sticky="w", padx=5, pady=5
)
end_date_entry = ttk.Entry(input_frame)
end_date_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
end_date_entry.insert(0, "2025-02-01")

input_frame.columnconfigure(1, weight=1)

run_button = ttk.Button(
    main_frame, text="Executar Backtest", command=run_backtest, style="Accent.TButton"
)
run_button.pack(pady=10)

output_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
output_frame.pack(fill="both", expand=True)

output_text = scrolledtext.ScrolledText(output_frame, width=80, height=20, wrap=tk.WORD)
output_text.pack(fill="both", expand=True, side="top", padx=5, pady=5)

copy_button = ttk.Button(
    output_frame, text="Copiar Resultados", command=copy_to_clipboard
)
copy_button.pack(pady=5, side="bottom")

style.configure("Accent.TButton", foreground="white", background="#0078D7")

root.mainloop()
