import pandas as pd
import yfinance as yf
import streamlit as st
import matplotlib

# Tous les éléments st sont dont éléments de streamlit, ils servent donc au visuel

#Paramètre de la page
st.set_page_config(
    page_title="Stratégie de Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

#Titre de la sidebar
st.sidebar.header("Menu")
#Page renvoie l'élément choisit dans la sidebar
page = st.sidebar.radio(label="",options=["Advanced", "Basic"])

#On affiche la page voulue en fonction de la page choisie dans la sidebar
#Advance correspond à la dernière version du projet
#L'autre page étant le backup de ce que l'on avait fait en première séance
if page == "Advanced":
    
    #Titre de la page et paramètres pour les stratégies
    st.header("📈 Stratégie sur les MAG 7")
    st.subheader("Manu va être content")
    fees = 0.005
    pctCash = 0.3
    tickers = ["NVDA","AAPL", "GOOGL", "MSFT","AMZN","TSLA","META"]

    # 1 ligne avec les différents paramètres modifiables depuis la page
    with st.form("Paramètres"):
        
        col1, col2, col3, col4 = st.columns([1, 2, 2,1])

        #Période de données depuis yfinance
        with col1:
            period = st.selectbox("Période", ["1mo", "3mo", "6mo", "1y", "2y", "5y"])

        #Retard pour la stratégie
        with col2:
            lag = st.number_input("Lag de la stratégie", min_value=1, step=1, value=2, format="%d")

        #Capital de départ
        with col3:
            portfolioInput = st.number_input("Capital de départ", min_value=500, value=10000, step=500)

        #Stop loss voulu (en %)
        with col4:
            stopLoss = 1 -st.number_input("Stop loss (%)", min_value=1, value=10, step=1,max_value=50)/100

        #Boutons pour lancer le calcul
        run = st.form_submit_button(label="Appliquer",type="primary")

    #Les calculs s'éxécutent dès que l'on appuit sur le bouton appliquer
    #Cela évite que tout le code se lance dès que l'on change un paramètre
    #(Par exemple quand on clic plusieurs fois pour augmenter le capital de départ)
    if run:
        #Données depuis yahoo finance
        data = yf.download(tickers, period=period, interval="1d", progress=False)["Close"]

        #Tout le reste s'affiche dans un cercle de chargement tant que ce n'est pas fini
        with st.spinner("Chargement"):

            class portfolioClass:
                
                #Etat initial du portfeuille
                def __init__(self, cash):
                    self.cash = cash
                    self.equities = {}
                    self.history = pd.DataFrame(columns=["Date","Ticker", "Order", "Number","Price","Active Position"])
                    self.total = cash

                #Méthode de mise à jour du portefeuille
                def update(self, cash, equities,day):
                    self.cash = cash
                    self.equities =equities
                    self.total = self.cash + sum(equities[i]*data.loc[day][i] for i in equities.keys())

            #Fonction d'achat
            def buy (data,portfolio,day,ticker):
                #Nombre d'actions que l'on peut acheter
                nbEquityBuy = int(portfolio.cash*pctCash / (data.loc[day][ticker]*(1+fees)))
                #Cash restant après l'achat
                newCash = portfolio.cash - (data.loc[day][ticker] * nbEquityBuy)*(1+fees)
                #Mise a jour des actions en portfeuille
                equities = portfolio.equities
                if ticker in equities.keys():
                    equities[ticker] = nbEquityBuy + equities[ticker]
                else:
                    equities[ticker] = nbEquityBuy
                #Ajout de l'ordre dans l'historique du portefeuille
                portfolio.history.loc[len(portfolio.history)]=[day,ticker,"Buy",nbEquityBuy,data.loc[day][ticker],True]
                #Mise à jour du portfeuille
                portfolio.update( newCash ,equities, day)

            #Fonction de vente
            def sell(data,portfolio,day,ticker, numberSell):
                #Cash restant après la vente
                newCash = portfolio.cash + numberSell*data.loc[day][ticker]*(1-fees)
                #Mise a jour des actions en portefeuille
                equities = portfolio.equities
                equities[ticker] = equities[ticker] - numberSell 
                #Ajout de l'ordre de vente dans l'historique du portefeuille
                portfolio.history.loc[len(portfolio.history)]=[day,ticker,"Sell",numberSell,data.loc[day][ticker],False]
                #Mise à jour du portfeuille
                portfolio.update( newCash ,equities, day)

            #Fonction qui contient toutes les stratégies en fonction de celle que l'on choisit
            #Non utilisée dans cette dernière version
            def strat (df,portfolio , day, stratNumber, paramStrat2 = 0, paramStrat3 = 0):
                
                #Stratégie 1
                #On achete à l'ouverture et on vend à la clôture
                if (stratNumber == 1):
                    nbEquityBuy = int(portfolio.cash / df.loc[day]["Open"])
                    newCash = portfolio.cash - df.loc[day]["Open"] * nbEquityBuy
                    portfolio.update( newCash + df.loc[day]["Close"]*nbEquityBuy ,0,0)

                #Stratégie 2
                #Si le rendement journalier est supérieur aux frais, on achète
                elif stratNumber == 2:
                    idx = df.index.get_loc(day)
                    if idx > paramStrat2:
                        if df.iloc[idx]["Close"]/df.iloc[idx-paramStrat2]["Close"] - 1 > fees:
                            buy(df,portfolio,day,idx)

                        elif df.iloc[idx]["Close"]/df.iloc[idx-paramStrat2]["Close"] -1 < -0.01:
                            sell(df,portfolio,day,idx)

                #Stratégie 3
                #Si le rendement journalier a été à la baisse pendant x jours de retard et que le dernier jour est à la hausse, on achète
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

            #Liste de la valeur du portfeuille
            ptfValue = []
            portfolio = portfolioClass(portfolioInput)
            #On parcours tous les jours des données pour éxécuter la stratégie chaque jour
            for day in data.index :
                idx = data.index.get_loc(day)
                if not idx < lag:
                    #on regarde pour toutes les actions
                    for ticker in tickers:
                        negative = True
                        #On s'assure que le rendement est bien négatif sur les x jour de lag
                        for i in range (idx-1,idx-lag-1,-1):
                            if data.iloc[i][ticker] > data.iloc[i-1][ticker]:
                                negative = False
                        #Si en plus le dernier rendement journalier est positif, on achète
                        if negative and data.iloc[idx][ticker]>data.iloc[idx-1][ticker]:
                            buy(data,portfolio,day,ticker)

                    #On parcours les positions actives dans l'historique pour voir si il faut vendre
                    active = portfolio.history.loc[portfolio.history["Active Position"]].copy()

                    for r in active.itertuples():
                        ticker = r.Ticker
                        buy_price = r.Price
                        price_today = data.loc[day, ticker]
                        price_yday  = data.iloc[idx-1][ticker]

                        #On vend si le stop loss est atteind ou si le prix baisse mais qu'il est supérieur au prix d'achat et des frais
                        if (price_today < buy_price * stopLoss) or (
                            (price_today < price_yday) and (price_today > buy_price * (1 + fees))
                        ):
                            sell(data, portfolio, day, ticker, r.Number)
                            portfolio.history.loc[r.Index, "Active Position"] = False
                
                portfolio.update( portfolio.cash, portfolio.equities,day)
                ptfValue.append(portfolio.total)

            #Data frame des valeurs de portefeuille pour un faire un graphique
            ptfValue = pd.DataFrame(index=data.index, data = ptfValue, columns=["Portfolio"])
            #Data frame avec les rendements du portefeuille et de chacune des actions sur la période
            outputDf = pd.DataFrame(index= ["Rendements en %", "Ecart-type"],data={"Stratégie" : [(ptfValue["Portfolio"].iloc[-1]/ptfValue["Portfolio"].iloc[0]-1)*100,round(ptfValue["Portfolio"].std(),2)]})
            for ticker in tickers:
                outputDf[ticker] = [round((data[ticker].iloc[-1]/data[ticker].iloc[0]-1)*100,2),round(data[ticker].std(),2)]
            try :
                #Affichage dans streamlit : titres, graphiques et tableaux
                st.subheader("Evolution du portefeuille")
                st.line_chart(ptfValue, y_label= "Valeur du portefeuille")
                st.subheader("Evolution des MAG 7")
                st.line_chart(data)
                st.dataframe(outputDf.style.format("{:.2f}").background_gradient(cmap="RdYlGn", axis=1, subset=pd.IndexSlice[["Rendements en %"], :]))
                st.metric("Rendement stratégie", f"{round((ptfValue["Portfolio"].iloc[-1]/ptfValue["Portfolio"].iloc[0]-1)*100,2)} %")
                for ticker in tickers:
                    st.metric(f"Rendement buy and hold de {ticker}", f"{round((data[ticker].iloc[-1]/data[ticker].iloc[0]-1)*100,2)} %")
                st.subheader("Historique de movements")
                st.dataframe(portfolio.history)
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

    except Exception as e:
        st.exception(e)