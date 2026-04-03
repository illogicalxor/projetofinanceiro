"""
Unified GUI application — consolidates all features from backtest.py, painel.py, painelg.py, etc.
"""

from datetime import datetime

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

import matplotlib
matplotlib.use("TkAgg")

from projetofinanceiro.core import (
    backtest_dca,
    backtest_lump_sum,
    plot_net_income,
    plot_adjusted_price,
    get_ipca_anual,
    simulate_tesouro_selic,
    plot_selic_evolucao,
    plot_bitcoin,
    plot_lucro_fundamentus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_float(entry: ttk.Entry, default: float) -> float:
    try:
        return float(entry.get())
    except (ValueError, tk.TclError):
        return default


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


def run_dca_backtest():
    output_text.delete("1.0", tk.END)
    tickers = tickers_entry.get().split()
    if not tickers:
        messagebox.showwarning("Atenção", "Informe ao menos um ticker.")
        return

    aporte = _safe_float(investment_entry, 1000)
    start = start_date_entry.get() or "2010-01-01"
    end = end_date_entry.get() or datetime.today().strftime("%Y-%m-%d")

    for t in tickers:
        try:
            result = backtest_dca(t, aporte, start, end)
            output_text.insert(tk.END,
                f"✅ {result['ticker']} — DCA (Total Return)\n"
                f"   Período: {result['data_inicio_real']} → {result['data_fim']}\n"
                f"   Total investido: R$ {result['total_investido']:,.2f}\n"
                f"   Patrimônio final: R$ {result['patrimonio_final']:,.2f}\n"
                f"   Lucro: R$ {result['lucro_abs']:,.2f} ({result['rentabilidade_pct']:.1f}%)\n"
                f"{'─' * 45}\n")
        except Exception as e:
            output_text.insert(tk.END, f"❌ {t}: {e}\n")


def run_lump_sum_backtest():
    output_text.delete("1.0", tk.END)
    tickers = tickers_entry.get().split()
    if not tickers:
        messagebox.showwarning("Atenção", "Informe ao menos um ticker.")
        return

    aporte = _safe_float(investment_entry, 10000)
    start = start_date_entry.get() or "2010-01-01"
    end = end_date_entry.get() or datetime.today().strftime("%Y-%m-%d")

    for t in tickers:
        try:
            result = backtest_lump_sum(t, aporte, start, end)
            output_text.insert(tk.END,
                f"✅ {result['ticker']} — Aporte Único (Total Return)\n"
                f"   Período: {result['data_inicio_real']} → {result['data_fim']}\n"
                f"   Investido: R$ {result['total_investido']:,.2f}\n"
                f"   Patrimônio final: R$ {result['patrimonio_final']:,.2f}\n"
                f"   Lucro: R$ {result['lucro_abs']:,.2f} ({result['rentabilidade_pct']:.1f}%)\n"
                f"{'─' * 45}\n")
        except Exception as e:
            output_text.insert(tk.END, f"❌ {t}: {e}\n")


def plot_lucro_brl():
    _plot_lucro("BRL")


def plot_lucro_usd():
    _plot_lucro("USD")


def _plot_lucro(mode: str):
    ticker = tickers_entry.get().strip().split()[0] if tickers_entry.get().strip() else "WEGE3"
    start = start_date_entry.get() or "2010-01-01"
    end = end_date_entry.get() or datetime.today().strftime("%Y-%m-%d")
    try:
        plot_net_income(ticker, mode=mode, start=start, end=end)
    except Exception as e:
        messagebox.showwarning("Informação", str(e))


def plot_preco_ajustado():
    ticker = tickers_entry.get().strip().split()[0] if tickers_entry.get().strip() else "WEGE3"
    start = start_date_entry.get() or "2000-01-01"
    end = end_date_entry.get() or datetime.today().strftime("%Y-%m-%d")
    try:
        plot_adjusted_price(ticker, start=start, end=end)
    except Exception as e:
        messagebox.showwarning("Informação", str(e))


def plot_fundamentus():
    ticker = tickers_entry.get().strip().split()[0] if tickers_entry.get().strip() else "WEGE3"
    try:
        plot_lucro_fundamentus(ticker)
    except Exception as e:
        messagebox.showwarning("Informação", str(e))


def run_selic():
    output_text.delete("1.0", tk.END)
    start = start_date_entry.get() or "2000-01-01"
    aporte = _safe_float(investment_entry, 1000)
    try:
        resultado = simulate_tesouro_selic(start, aporte)
        output_text.insert(tk.END,
            f"📈 Tesouro Selic\n"
            f"   Total investido: R$ {resultado['total_aportes']:,.2f}\n"
            f"   Patrimônio final: R$ {resultado['patrimonio_final']:,.2f}\n")
        plot_selic_evolucao(start, aporte)
    except Exception as e:
        messagebox.showerror("Erro", str(e))


def run_ipca():
    output_text.delete("1.0", tk.END)
    try:
        df = get_ipca_anual()
        output_text.insert(tk.END, "📊 IPCA Anual:\n")
        for _, row in df.iterrows():
            output_text.insert(tk.END, f"   {int(row['ano'])}: {row['inflacao_acumulada']:.2f}%\n")
    except Exception as e:
        messagebox.showerror("Erro", str(e))


def run_bitcoin():
    output_text.delete("1.0", tk.END)
    try:
        plot_bitcoin()
    except Exception as e:
        messagebox.showerror("Erro", str(e))


def copy_results():
    text = output_text.get("1.0", tk.END).strip()
    if text:
        root.clipboard_clear()
        root.clipboard_append(text)
        messagebox.showinfo("Copiado", "Resultados copiados para a área de transferência.")


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

root = tk.Tk()
root.title("Projeto Financeiro — Painel Unificado")
root.geometry("800x650")

style = ttk.Style()
style.theme_use("clam")

main = ttk.Frame(root, padding=15)
main.pack(fill="both", expand=True)

# --- Configurações ---
cfg = ttk.LabelFrame(main, text=" Configurações ", padding=10)
cfg.pack(fill="x", pady=5)

ttk.Label(cfg, text="Tickers (ex: WEGE3 PETR4 AAPL):").grid(row=0, column=0, sticky="w")
tickers_entry = ttk.Entry(cfg, width=40)
tickers_entry.grid(row=0, column=1, sticky="ew", padx=5)
tickers_entry.insert(0, "WEGE3")

ttk.Label(cfg, text="Aporte Mensal R$:").grid(row=1, column=0, sticky="w")
investment_entry = ttk.Entry(cfg)
investment_entry.grid(row=1, column=1, sticky="ew", padx=5)
investment_entry.insert(0, "1000")

ttk.Label(cfg, text="Data Início:").grid(row=2, column=0, sticky="w")
start_date_entry = ttk.Entry(cfg)
start_date_entry.grid(row=2, column=1, sticky="ew", padx=5)
start_date_entry.insert(0, "2010-01-01")

ttk.Label(cfg, text="Data Fim:").grid(row=3, column=0, sticky="w")
end_date_entry = ttk.Entry(cfg)
end_date_entry.grid(row=3, column=1, sticky="ew", padx=5)
end_date_entry.insert(0, datetime.today().strftime("%Y-%m-%d"))

cfg.columnconfigure(1, weight=1)

# --- Botões Backtest ---
bf = ttk.LabelFrame(main, text=" Backtest ", padding=10)
bf.pack(fill="x", pady=5)

ttk.Button(bf, text="DCA (Aportes Mensais)", command=run_dca_backtest).grid(row=0, column=0, padx=5, pady=5)
ttk.Button(bf, text="Aporte Único (Lump Sum)", command=run_lump_sum_backtest).grid(row=0, column=1, padx=5, pady=5)

# --- Botões Gráficos ---
gf = ttk.LabelFrame(main, text=" Gráficos ", padding=10)
gf.pack(fill="x", pady=5)

ttk.Button(gf, text="Lucro (R$)", command=plot_lucro_brl).grid(row=0, column=0, padx=5, pady=5)
ttk.Button(gf, text="Lucro (USD)", command=plot_lucro_usd).grid(row=0, column=1, padx=5, pady=5)
ttk.Button(gf, text="Preço Ajustado", command=plot_preco_ajustado).grid(row=0, column=2, padx=5, pady=5)
ttk.Button(gf, text="Lucro (Fundamentus)", command=plot_fundamentus).grid(row=0, column=3, padx=5, pady=5)

# --- Botões Indicadores ---
ind = ttk.LabelFrame(main, text=" Indicadores Econômicos ", padding=10)
ind.pack(fill="x", pady=5)

ttk.Button(ind, text="Tesouro Selic", command=run_selic).grid(row=0, column=0, padx=5, pady=5)
ttk.Button(ind, text="IPCA", command=run_ipca).grid(row=0, column=1, padx=5, pady=5)
ttk.Button(ind, text="Bitcoin", command=run_bitcoin).grid(row=0, column=2, padx=5, pady=5)

# --- Resultados ---
output_text = scrolledtext.ScrolledText(main, height=18, font=("Courier", 10))
output_text.pack(fill="both", expand=True, pady=5)

ttk.Button(main, text="Copiar Resultados", command=copy_results).pack(pady=5)

root.mainloop()
