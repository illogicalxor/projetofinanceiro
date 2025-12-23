import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt


def plot_lucro_brl_e_usd(ticker):
    # =========================
    # Lucro líquido (BRL)
    # =========================
    acao = yf.Ticker(ticker)
    financials = acao.financials

    if financials.empty or "Net Income" not in financials.index:
        raise ValueError("Lucro líquido não encontrado para este ticker.")

    lucro_brl = financials.loc["Net Income"].sort_index()
    anos = lucro_brl.index.year

    # =========================
    # Dólar histórico (USD/BRL)
    # =========================
    usd = yf.Ticker("USDBRL=X")

    start_date = f"{anos.min()}-01-01"
    end_date = f"{anos.max()}-12-31"

    cambio = usd.history(start=start_date, end=end_date)

    if cambio.empty:
        raise ValueError("Não foi possível obter o câmbio USD/BRL.")

    dolar_medio_anual = cambio["Close"].groupby(cambio.index.year).mean()

    # =========================
    # Converter lucro para USD
    # =========================
    lucro_df = pd.DataFrame(
        {
            "Lucro_BRL": lucro_brl.values,
        },
        index=anos,
    )

    lucro_df["USD_BRL"] = dolar_medio_anual
    lucro_df["Lucro_USD"] = lucro_df["Lucro_BRL"] / lucro_df["USD_BRL"]

    lucro_df = lucro_df.dropna()

    # =========================
    # Plot 1 — Lucro em Reais
    # =========================
    plt.figure()
    plt.plot(lucro_df.index, lucro_df["Lucro_BRL"] / 1e9, marker="o")
    plt.xlabel("Ano")
    plt.ylabel("Lucro (R$ bilhões)")
    plt.title(f"Lucro em Reais — {ticker}")
    plt.grid(True)
    plt.show()

    # =========================
    # Plot 2 — Lucro em Dólares
    # =========================
    plt.figure()
    plt.plot(lucro_df.index, lucro_df["Lucro_USD"] / 1e9, marker="o")
    plt.xlabel("Ano")
    plt.ylabel("Lucro (USD bilhões)")
    plt.title(f"Lucro em Dólares — {ticker}")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    ticker = input("Digite o ticker (ex: WEGE3.SA): ").strip()
    plot_lucro_brl_e_usd(ticker)
