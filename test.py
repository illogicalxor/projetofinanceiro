import yfinance as yf
import pandas as pd

ticker = input("Digite o ticker: ")

# Ajuste automático do ticker brasileiro
if not ticker.endswith(".SA"):
    ticker = ticker + ".SA"

start = "2000-01-01"
end = "2025-12-31"

stock = yf.Ticker(ticker)

# Preço ajustado (inclui reinvestimento implícito)
hist = stock.history(start=start, end=end, auto_adjust=True)

# Apenas preço ajustado
df = hist[["Close"]].reset_index()
df.columns = ["Date", "Close"]

print("\n--- Últimos 48 dividendos (fonte: stock.actions) ---")
try:
    dividends = stock.actions["Dividends"].dropna()
    last48 = dividends.tail(48)

    print(last48)

    # Soma dos últimos 48 dividendos
    soma = last48.sum()
    print(f"\nSoma dos últimos 48 dividendos: R$ {soma:.2f}")

except Exception as e:
    print("Sem dividendos ou erro ao obter dividendos.")
    print(e)
