import pandas as pd
import yfinance as yf
import streamlit as st


st.set_page_config(
    page_title="Stratégie de Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.header("Menu")
page = st.sidebar.radio(label="",options=["Advanced", "Basic"])
if page == "Advanced":
    st.header("📈 Stratégie sur les MAG 7")
    st.subheader("Manu va être content")
    fees = 0.005
    pctCash = 0.3
    tickers = ["NVDA","AAPL", "GOOGL", "MSFT","AMZN","TSLA","META"]
    stopLoss = 0.9

    with st.form("Paramètres"):
        
        col1, col2, col3, col4, col5 = st.columns([1, 2, 2,1,1])

        with col1:
            period = st.selectbox("Période", ["1mo", "3mo", "6mo", "1y", "2y", "5y"])

        with col2:
            lag = st.number_input("Lag de la stratégie", min_value=1, step=1, value=2, format="%d")

        with col3:
            portfolioInput = st.number_input("Capital de départ", min_value=500, value=10000, step=500)

        with col4:
            stopLoss = 1 -st.number_input("Stop loss (%)", min_value=1, value=10, step=1,max_value=50)/100

        with col5:
            run = st.form_submit_button(label="Appliquer",type="primary")

    if run:
        data = yf.download(tickers, period=period, interval="1d", progress=False)["Close"]

        with st.spinner("Chargement"):
            class portfolioClass:
                
                def __init__(self, cash):
                    self.cash = cash
                    self.equities = {}
                    self.history = pd.DataFrame(columns=["Date","Ticker", "Order", "Number","Price","Active Position"])
                    self.total = cash

                def update(self, cash, equities,day):
                    self.cash = cash
                    self.equities =equities
                    # self.history = historyDf
                    self.total = self.cash + sum(equities[i]*data.loc[day][i] for i in equities.keys())

            ptfValue = pd.DataFrame()

            def buy (data,portfolio,day,ticker):
                nbEquityBuy = int(portfolio.cash*pctCash / (data.loc[day][ticker]*(1+fees)))
                newCash = portfolio.cash - (data.loc[day][ticker] * nbEquityBuy)*(1+fees)
                equities = portfolio.equities
                if ticker in equities.keys():
                    equities[ticker] = nbEquityBuy + equities[ticker]
                else:
                    equities[ticker] = nbEquityBuy
                portfolio.history.loc[len(portfolio.history)]=[day,ticker,"Buy",nbEquityBuy,data.loc[day][ticker],True]
                portfolio.update( newCash ,equities, day)

            def sell(data,portfolio,day,ticker, numberSell):
                newCash = portfolio.cash + numberSell*data.loc[day][ticker]*(1-fees)
                equities = portfolio.equities
                equities[ticker] = equities[ticker] - numberSell 
                portfolio.history.loc[len(portfolio.history)]=[day,ticker,"Sell",numberSell,data.loc[day][ticker],False]
                portfolio.update( newCash ,equities, day)

            def strat (df,portfolio , day, stratNumber, paramStrat2 = 0, paramStrat3 = 0):

                if (stratNumber == 1):
                    nbEquityBuy = int(portfolio.cash / df.loc[day]["Open"])
                    newCash = portfolio.cash - df.loc[day]["Open"] * nbEquityBuy
                    portfolio.update( newCash + df.loc[day]["Close"]*nbEquityBuy ,0,0)

                elif stratNumber == 2:
                    idx = df.index.get_loc(day)
                    if idx > paramStrat2:
                        if df.iloc[idx]["Close"]/df.iloc[idx-paramStrat2]["Close"] - 1 > fees:
                            buy(df,portfolio,day,idx)

                        elif df.iloc[idx]["Close"]/df.iloc[idx-paramStrat2]["Close"] -1 < -0.01:
                            sell(df,portfolio,day,idx)

                elif stratNumber == 3:
                    idx = df.index.get_loc(day)
                    if idx> paramStrat3:
                        negative = True
                        for i in range (-2,-paramStrat3-1,-1):
                            if df.iloc[i+1]["Close"] > df.iloc[i]["Close"]:
                                negative = False
                        if not negative and df.iloc[idx]["Close"]>df.iloc[idx-1]["Close"]:
                            buy(df,portfolio,day,idx)
                        elif df.iloc[idx]["Close"]<df.iloc[idx-1]["Close"] and portfolio.nbEquity > 0 and df.iloc[idx]["Close"]> portfolio.priceEquity*(1+fees):
                            sell(df,portfolio,day,idx)

            ptfValue = []
            portfolio = portfolioClass(portfolioInput)
            for day in data.index :
                idx = data.index.get_loc(day)
                if not idx < lag:
                    for ticker in tickers:
                        negative = True
                        for i in range (idx-1,idx-lag-1,-1):
                            if data.iloc[i][ticker] > data.iloc[i-1][ticker]:
                                negative = False
                        if negative and data.iloc[idx][ticker]>data.iloc[idx-1][ticker]:
                            buy(data,portfolio,day,ticker)

                    active = portfolio.history.loc[portfolio.history["Active Position"]].copy()

                    for r in active.itertuples():
                        ticker = r.Ticker
                        buy_price = r.Price
                        price_today = data.loc[day, ticker]
                        price_yday  = data.iloc[idx-1][ticker]

                        if (price_today < buy_price * stopLoss) or (
                            (price_today < price_yday) and (price_today > buy_price * (1 + fees))
                        ):
                            sell(data, portfolio, day, ticker, r.Number)
                            portfolio.history.loc[r.Index, "Active Position"] = False
                
                portfolio.update( portfolio.cash, portfolio.equities,day)
                ptfValue.append(portfolio.total)

            ptfValue = pd.DataFrame(index=data.index, data = ptfValue, columns=["Portfolio"])
            outputDf = pd.DataFrame(index= ["Rendements en %", "Ecart-type"],data={"Stratégie" : [(ptfValue["Portfolio"].iloc[-1]/ptfValue["Portfolio"].iloc[0]-1)*100,round(ptfValue["Portfolio"].std(),2)]})
            for ticker in tickers:
                outputDf[ticker] = [round((data[ticker].iloc[-1]/data[ticker].iloc[0]-1)*100,2),round(data[ticker].std(),2)]
            try :
                st.subheader("Evolution du portefeuille")
                st.line_chart(ptfValue, y_label= "Valeur du portefeuille")
                st.subheader("Evolution des MAG 7")
                st.line_chart(data)
                st.table(outputDf)
                st.metric("Rendement stratégie", f"{round((ptfValue["Portfolio"].iloc[-1]/ptfValue["Portfolio"].iloc[0]-1)*100,2)} %")
                for ticker in tickers:
                    st.metric(f"Rendement buy and hold de {ticker}", f"{round((data[ticker].iloc[-1]/data[ticker].iloc[0]-1)*100,2)} %")
            except Exception as e:
                st.exception(e)

if page == "Basic":
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