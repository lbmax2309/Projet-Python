import yfinance as yf

tickers = ["NVDA","AAPL", "GOOGL"]
stopLoss = 0.9

data = yf.download(
    tickers,
    period="5y",
    interval="1d",
    group_by="column",
    auto_adjust=False,
    threads=True,
)["Close"]

print(i for i in data.iterrows())