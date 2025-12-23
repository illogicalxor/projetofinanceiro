import yfinance as yf
import pandas as pd
import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib.pyplot as plt


# ======================================================
# DADOS FUNDAMENTALISTAS
# ======================================================


def get_lucro_anual(ticker):
    stock = yf.Ticker(ticker)
    financials = stock.financials

    if financials.empty or "Net Income" not in financials.index:
        raise ValueError("Lucro líquido não disponível.")

    lucro = financials.loc["Net Income"].sort_index()
    lucro.index = lucro.index.year
    return lucro


def converter_lucro_usd(lucro_brl):
    usd = yf.Ticker("USDBRL=X")

    start = f"{lucro_brl.index.min()}-01-01"
    end = f"{lucro_brl.index.max()}-12-31"

    cambio = usd.history(start=start, end=end)

    if cambio.empty:
        raise ValueError("Não foi possível obter o câmbio USD/BRL.")

    dolar_medio = cambio["Close"].groupby(cambio.index.year).mean()

    df = pd.DataFrame({"Lucro_BRL": lucro_brl, "USD_BRL": dolar_medio}).dropna()

    df["Lucro_USD"] = df["Lucro_BRL"] / df["USD_BRL"]
    return df


# ======================================================
# GRÁFICOS
# ======================================================


def plot_lucro_brl(ticker):
    lucro = get_lucro_anual(ticker)

    plt.figure()
    plt.plot(lucro.index, lucro.values / 1e9, marker="o")
    plt.title(f"Lucro em Reais — {ticker}")
    plt.xlabel("Ano")
    plt.ylabel("R$ bilhões")
    plt.grid(True)
    plt.show()


def plot_lucro_usd(ticker):
    lucro = get_lucro_anual(ticker)
    df = converter_lucro_usd(lucro)

    plt.figure()
    plt.plot(df.index, df["Lucro_USD"] / 1e9, marker="o")
    plt.title(f"Lucro em Dólares — {ticker}")
    plt.xlabel("Ano")
    plt.ylabel("USD bilhões")
    plt.grid(True)
    plt.show()


# ======================================================
# BACKTEST DE APORTES MENSAIS
# ======================================================


def get_stock_data(ticker, monthly_investment, start, end):
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start, end=end, auto_adjust=True)

    if hist.empty:
        return "Erro ao obter dados.", 0, 0, None

    hist = hist.dropna(subset=["Close"])
    first_valid_date = hist.index.min().date()

    df = hist[["Close"]].reset_index()
    df.columns = ["Date", "Close"]

    df["Month"] = df["Date"].dt.to_period("M")
    investment_days = df.groupby("Month")["Date"].first()
    investment_days_set = set(investment_days)

    shares = 0
    total_aportes = 0

    for _, row in df.iterrows():
        if row["Date"] in investment_days_set and row["Close"] > 0:
            shares += monthly_investment / row["Close"]
            total_aportes += monthly_investment

    patrimonio = shares * df.iloc[-1]["Close"]
    return None, patrimonio, total_aportes, first_valid_date


# ======================================================
# GUI CALLBACKS
# ======================================================


def run_backtest():
    output_text.delete("1.0", tk.END)

    tickers = tickers_entry.get().strip().split()
    aporte = float(investment_entry.get() or 1000)
    start = start_date_entry.get() or "2000-01-01"
    end = end_date_entry.get() or "2025-01-01"

    total = 0
    investido = 0

    for ticker in tickers:
        if ticker[-1] in "341":
            ticker += ".SA"

        err, patrimonio, aportes, data = get_stock_data(ticker, aporte, start, end)

        if err:
            output_text.insert(tk.END, f"{ticker}: {err}\n")
        else:
            total += patrimonio
            investido += aportes
            output_text.insert(
                tk.END,
                f"{ticker}: Patrimônio R${patrimonio:,.2f} | "
                f"Aportado R${aportes:,.2f} | "
                f"Desde {data}\n",
            )

    output_text.insert(
        tk.END,
        f"\nTOTAL PORTFÓLIO: R${total:,.2f}\nTOTAL INVESTIDO: R${investido:,.2f}\n",
    )


def gerar_lucro_brl():
    ticker = tickers_entry.get().strip()
    if ticker and ticker[-1] in "341":
        ticker += ".SA"
    plot_lucro_brl(ticker)


def gerar_lucro_usd():
    ticker = tickers_entry.get().strip()
    if ticker and ticker[-1] in "341":
        ticker += ".SA"
    plot_lucro_usd(ticker)


def copy_to_clipboard():
    root.clipboard_clear()
    root.clipboard_append(output_text.get("1.0", tk.END))


# ======================================================
# GUI
# ======================================================

root = tk.Tk()
root.title("Painel Buy & Hold — BRL / USD")
root.geometry("700x550")

style = ttk.Style(root)
style.theme_use("clam")

main = ttk.Frame(root, padding=10)
main.pack(fill="both", expand=True)

params = ttk.LabelFrame(main, text="Parâmetros", padding=10)
params.pack(fill="x")

ttk.Label(params, text="Tickers:").grid(row=0, column=0, sticky="w")
tickers_entry = ttk.Entry(params, width=40)
tickers_entry.grid(row=0, column=1, sticky="ew")
tickers_entry.insert(0, "WEGE3")

ttk.Label(params, text="Aporte Mensal:").grid(row=1, column=0, sticky="w")
investment_entry = ttk.Entry(params)
investment_entry.grid(row=1, column=1, sticky="ew")
investment_entry.insert(0, "1000")

ttk.Label(params, text="Data início:").grid(row=2, column=0, sticky="w")
start_date_entry = ttk.Entry(params)
start_date_entry.grid(row=2, column=1, sticky="ew")
start_date_entry.insert(0, "2000-01-01")

ttk.Label(params, text="Data fim:").grid(row=3, column=0, sticky="w")
end_date_entry = ttk.Entry(params)
end_date_entry.grid(row=3, column=1, sticky="ew")
end_date_entry.insert(0, "2025-01-01")

params.columnconfigure(1, weight=1)

ttk.Button(main, text="Executar Backtest", command=run_backtest).pack(pady=5)

buttons = ttk.Frame(main)
buttons.pack(pady=5)

ttk.Button(buttons, text="Gráfico Lucro (R$)", command=gerar_lucro_brl).grid(
    row=0, column=0, padx=5
)
ttk.Button(buttons, text="Gráfico Lucro (USD)", command=gerar_lucro_usd).grid(
    row=0, column=1, padx=5
)

output = ttk.LabelFrame(main, text="Resultados", padding=10)
output.pack(fill="both", expand=True)

output_text = scrolledtext.ScrolledText(output, height=15)
output_text.pack(fill="both", expand=True)

ttk.Button(output, text="Copiar", command=copy_to_clipboard).pack(pady=5)

root.mainloop()
