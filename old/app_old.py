import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import streamlit as st



st.header("Projet Python")
capitalInput = 1000
fees = 0.005
ticker = st.selectbox("Merci de choisir une action :", ["NVDA","AAPL"])
strat1 = st.checkbox("Stratégie 1 :")
strat2 = st.checkbox("Stratégie 2 :")
strat3 = st.checkbox("Stratégie 3 :")

class capitalClass:
    
    def __init__(self, cash, nbEquity, priceEquity):
        self.cash = cash
        self.nbEquity = nbEquity
        self.priceEquity =priceEquity
        self.ptfValue = nbEquity * priceEquity
        self.total = self.cash + self.ptfValue

    def update(self, cash, nbEquity, priceEquity):
        self.nbEquity = nbEquity
        self.priceEquity =priceEquity
        self.cash = cash
        self.ptfValue = nbEquity * priceEquity
        self.total = self.ptfValue + self.cash


ptfValue = pd.DataFrame()

def buy (df,capital,day,idx):
    nbEquityBuy = int(capital.cash / (df.loc[day]["Close"]*(1+fees)))
    newCash = capital.cash - (df.loc[day]["Close"] * nbEquityBuy)*(1+fees)
    capital.update( newCash ,nbEquityBuy + capital.nbEquity, df.iloc[idx]["Close"])

def sell(df,capital,day,idx):
    newCash = (capital.nbEquity * df.iloc[idx]["Close"]) * (1-fees) + capital.cash
    capital.update( newCash ,0, 0)


def strat (df,capital , day, stratNumber, paramStrat2 = 0, paramStrat3 = 0):

    if (stratNumber == 1):
        nbEquityBuy = int(capital.cash / df.loc[day]["Open"])
        newCash = capital.cash - df.loc[day]["Open"] * nbEquityBuy
        capital.update( newCash + df.loc[day]["Close"]*nbEquityBuy ,0,0)

    elif stratNumber == 2:
        idx = df.index.get_loc(day)
        if idx > paramStrat2:
            if df.iloc[idx]["Close"]/df.iloc[idx-paramStrat2]["Close"] - 1 > fees:
                buy(df,capital,day,idx)

            elif df.iloc[idx]["Close"]/df.iloc[idx-paramStrat2]["Close"] -1 < -0.01:
                sell(df,capital,day,idx)

    elif stratNumber == 3:
        idx = df.index.get_loc(day)
        if idx> paramStrat3:
            negative = True
            for i in range (-2,-paramStrat3-1,-1):
                if df.iloc[i+1]["Close"] > df.iloc[i]["Close"]:
                    negative = False
            if not negative and df.iloc[idx]["Close"]>df.iloc[idx-1]["Close"]:
                lastPrice = df.iloc[idx]["Close"]
                buy(df,capital,day,idx)
            elif df.iloc[idx]["Close"]<df.iloc[idx-1]["Close"] and capital.nbEquity > 0 and df.iloc[idx]["Close"]>capital.priceEquity*(1+fees):
                sell(df,capital,day,idx)

            

data = yf.Ticker(ticker).history(period="1y")
data = data[["Open","Close"]]

if strat1:
    capital = capitalClass (float(capitalInput), 0.0, 0.0)
    values = []
    for i in data.index:
        strat(data, capital,i,1)
        values.append(capital.total)
    ptfValue[ticker+ f"_Strat1"] = values



if strat2:
    for x in range(5,25,5):
        capital = capitalClass (float(capitalInput), 0.0, 0.0)
        values = []
        for i in data.index:
            strat( data, capital, i,2,x)
            values.append(capital.total)
        ptfValue[ticker+ f"_{x}"] = values

# if strat3 :
capital = capitalClass (float(capitalInput), 0.0, 0.0)
values = []
for i in data.index:
    strat( df=data, capital=capital, day=i,stratNumber=3,paramStrat2=0,paramStrat3=3)
    values.append(capital.total)
ptfValue[ticker+ f"_strat3"] = values

try :
    st.line_chart(ptfValue)
    st.line_chart(data["Close"])

except :
    None