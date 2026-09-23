import yfinance as yf
from scipy.stats import norm
import pandas as pd
import numpy as np

#initialising formulas for Black-Scholes option prices, delta and gamma, assuming no dividends
def B_S(S, K, r, sigma, T, type = "Call"):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if type == "Call":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

#computing delta as the derivative of the Black-Scholes price
def delta(S, K, r, sigma, T, type = "Call"):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    if type == "Call":
        return norm.cdf(d1)
    else:
        return norm.cdf(d1) - 1

#computing gamma as the derivative of the delta
def gamma(S, K, r, sigma, T):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return norm.pdf(d1) / (S * sigma * np.sqrt(T))

#setting the risk-free interest rate to be the mean 30-day UK risk-free rate over the last 10 years
r = 0.02

ticker = "SHEL"  # Shell stock
start_date = "2018-03-09"
end_date = "2018-04-23" #defining end date to be 2 weeks + 31 days after start date to use 2 weeks realised volatility to estimate implied volatility

data = yf.download(ticker, start=start_date, end=end_date) #fetching historical stock data
close = data["Close"].to_numpy().flatten()
dates = data.index

#computing and annualising volatility
log_returns = np.log(close[1:]/close[:-1])
sigma = np.std(log_returns[:10]) * np.sqrt(252)

option_start_date = pd.Timestamp(dates[11])
expiry_date = option_start_date + pd.Timedelta(days=30) #30 calendar day option

#choosing strike
S0 = close[11]
K = S0

days_remaining = (expiry_date - option_start_date).days
T = days_remaining / 365

option_price = B_S(S0, K, r, sigma, T, "Call")
option_delta = delta(S0, K, r, sigma, T, "Call")
option_gamma = gamma(S0, K, r, sigma, T)

#initialising delta for 10 call option contracts, each controlling 100 shares
contracts = 10
multiplier = 100
stock_position = 0
cash = 0 #initialising liquid cash amount
option_position_delta = contracts * multiplier * option_delta
option_position_gamma = contracts * multiplier * option_gamma

#setting tolerance limits based off initial absolute values
delta_tolerance = 0.1 * abs(option_position_delta)
gamma_tolerance = 0.1 * abs(option_position_gamma)

def delta_hedge():
    shares_to_trade = round(-option_position_delta)
    stock_position += shares_to_trade
    #positive stock position corresponds to a long position whereas a negative position corresponds to a short
    #the rounding corresponds to immediately shorting that number of shares after purchasing the option

    portfolio_values = []
    portfolio_deltas = []
    portfolio_gammas = []
    stock_trades = []
    unhedged_option_values = []

    #calculating and storing values after the initial hedge
    portfolio_delta = option_position_delta + stock_position
    portfolio_gamma = option_position_gamma
    option_value = contracts * multiplier * option_price
    stock_value = stock_position * S0
    cash += -stock_value -option_value #updating cash after buying option and shorting shares

    portfolio_values.append(0) #the portfolio value on the first day is still 0 since the stock price hasn't changed yet
    portfolio_deltas.append(portfolio_delta)
    portfolio_gammas.append(portfolio_gamma)
    stock_trades.append(shares_to_trade)
    unhedged_option_values.append(contracts * multiplier * option_price)

    for i in range(12, len(close)): #starting the loop the day after the option was bought, since delta was balanced immediately after
        current_date = pd.Timestamp(dates[i])
        days_remaining = (expiry_date - current_date).days
        S = close[i]
        if days_remaining == 0: # calculate terminal option payoff separately since B-S formula breaks down there
            option_price = max(S - K, 0)
            option_delta = 0
            option_gamma = 0 #not hedging on the final day since the option has expired
        else:
            T = days_remaining / 365
            sigma = np.std(log_returns[i - 10:i]) * np.sqrt(252)

            option_price = B_S(S, K, r, sigma, T, "Call")
            option_delta = delta(S, K, r, sigma, T, "Call")
            option_gamma = gamma(S, K, r, sigma, T)

        #computing new delta and gamma and initialising the net portfolio delta and gamma
        option_position_delta = contracts * multiplier * option_delta
        option_position_gamma = contracts * multiplier * option_gamma

        portfolio_delta = option_position_delta + stock_position
        portfolio_gamma = option_position_gamma

        #the delta hedge
        if abs(portfolio_delta) > delta_tolerance:
            shares_to_trade = round(-portfolio_delta) #positive shares to trade is taken to mean about to buy that no. shares, negative to selling that much
            stock_position += shares_to_trade
            cash -= shares_to_trade * S
            portfolio_delta += shares_to_trade

        option_value = contracts * multiplier * option_price
        stock_value = stock_position * S
        portfolio_value = option_value + stock_value + cash

        portfolio_values.append(portfolio_value)
        portfolio_deltas.append(portfolio_delta)
        portfolio_gammas.append(portfolio_gamma)
        stock_trades.append(shares_to_trade)
        unhedged_option_values.append(contracts * multiplier * option_price)

    portfolio_values = np.array(portfolio_values)
    portfolio_deltas = np.array(portfolio_deltas)
    portfolio_gammas = np.array(portfolio_gammas)
    stock_trades = np.array(stock_trades)
    unhedged_option_values = np.array(unhedged_option_values)

    #P&L volatility for hedged and unhedged portfolios
    hedged_pnl = np.diff(portfolio_values)
    hedged_volatility = np.std(hedged_pnl)
    unhedged_pnl = np.diff(unhedged_option_values)
    unhedged_volatility = np.std(unhedged_pnl)

    hedging_effiency = 1 - hedged_volatility / unhedged_volatility

    #mean absolute delta and gamma
    mean_abs_delta = np.mean(np.abs(portfolio_deltas))
    mean_abs_gamma = np.mean(np.abs(portfolio_gammas))

    #stock turnover
    stock_turnover = np.sum(np.abs(stock_trades))

    return [hedged_volatility, hedging_effiency, mean_abs_delta, mean_abs_gamma, stock_turnover]

def gamma_hedge():
    #initialising synthetic option market with strike prices at 0.8, 0.9, ..., 1.2 the current price
    moneyness_grid = np.array([0.8, 0.9, 1.0, 1.1, 1.2])
    best_option = None
    min_abs_n = float("inf") #choosing a second option contract such that it minimises the no. these contracts

    for moneyness in moneyness_grid:
        hedge_K = moneyness * S0
        for hedge_type in ["Call", "Put"]:
            hedge_gamma = gamma(S0, hedge_K, r, sigma, T)
            #no. contracts required to neutralise Gamma
            n = round(-option_position_gamma / (multiplier * hedge_gamma))

            #not using the exact same contract as the original ATM call
            if hedge_type == "Call" and moneyness == 1.0:
                continue

            if abs(n) < min_abs_n:
                min_abs_n = abs(n)
                best_option = {
                    "K": hedge_K,
                    "moneyness": moneyness,
                    "type": hedge_type,
                    "gamma": hedge_gamma,
                    "contracts": n
                }
    hedge_K = best_option["K"]
    hedge_type = best_option["type"]
    hedge_contracts = best_option["contracts"]

    hedge_option_price = B_S(S0, hedge_K, r, sigma, T, hedge_type)
    hedge_option_delta = delta(S0, hedge_K, r, sigma, T, hedge_type)
    hedge_option_gamma = gamma(S0, hedge_K, r, sigma, T)

    #initial gamma hedge
    hedge_position_gamma = hedge_contracts * multiplier * hedge_option_gamma
    portfolio_gamma = option_position_gamma + hedge_position_gamma

    #delta after gamma hedge
    hedge_position_delta = hedge_contracts * multiplier * hedge_option_delta
    net_option_delta = option_position_delta + hedge_position_delta

    shares_to_trade = round(-net_option_delta)
    stock_position += shares_to_trade
    portfolio_delta = net_option_delta + stock_position

    portfolio_values = []
    portfolio_deltas = []
    portfolio_gammas = []
    stock_trades = []
    unhedged_option_values = []
    
    #calculating and storing values after the initial hedge
    option_value = contracts * multiplier * option_price
    hedge_option_value = hedge_contracts * multiplier * hedge_option_price
    stock_value = stock_position * S0
    cash += -stock_value -option_value -hedge_option_value

    portfolio_values.append(0)
    portfolio_deltas.append(portfolio_delta)
    portfolio_gammas.append(portfolio_gamma)
    stock_trades.append(shares_to_trade)
    unhedged_option_values.append(contracts * multiplier * option_price)

    for i in range(12, len(close)):
        current_date = pd.Timestamp(dates[i])
        days_remaining = (expiry_date - current_date).days
        S = close[i]
        if days_remaining == 0:
            option_price = max(S - K, 0)
            if hedge_type == "Call":
                hedge_option_price = max(S - hedge_K, 0)
            else:
                hedge_option_price = max(hedge_K - S, 0)
            option_delta = option_gamma = 0
            hedge_option_delta = hedge_option_gamma = 0
        else:
            T = days_remaining / 365
            sigma = np.std(log_returns[i - 10:i]) * np.sqrt(252)

            option_price = B_S(S, K, r, sigma, T, "Call")
            option_delta = delta(S, K, r, sigma, T, "Call")
            option_gamma = gamma(S, K, r, sigma, T)
            hedge_option_price = B_S(S, hedge_K, r, sigma, T, hedge_type)
            hedge_option_delta = delta(S, hedge_K, r, sigma, T, hedge_type)
            hedge_option_gamma = gamma(S, hedge_K, r, sigma, T)

            option_position_delta = contracts * multiplier * option_delta
            option_position_gamma = contracts * multiplier * option_gamma
            hedge_option_delta = hedge_contracts * multiplier * hedge_position_delta
            hedge_option_gamma = hedge_contracts * multiplier * hedge_position_gamma

            portfolio_delta = option_position_delta + hedge_option_delta + stock_position
            portfolio_gamma = option_position_gamma + hedge_option_gamma

        #the gamma hedge
        if abs(portfolio_gamma) > gamma_tolerance:
            options_to_trade = round(-portfolio_gamma / hedge_option_gamma)
            hedge_contracts += options_to_trade
            cash -= options_to_trade * multiplier * hedge_option_price
            portfolio_gamma += options_to_trade * hedge_option_gamma
            portfolio_delta += options_to_trade * hedge_option_delta

        #the delta hedge, identical to before
        if abs(portfolio_delta) > delta_tolerance:
            shares_to_trade = round(-portfolio_delta)
            stock_position += shares_to_trade
            cash -= shares_to_trade * S
            portfolio_delta += shares_to_trade

        option_value = contracts * multiplier * option_price
        hedge_option_value = hedge_contracts * multiplier * hedge_option_price
        stock_value = stock_position * S
        portfolio_value = option_value + hedge_option_value + stock_value + cash
        
        portfolio_values.append(portfolio_value)
        portfolio_deltas.append(portfolio_delta)
        portfolio_gammas.append(portfolio_gamma)
        stock_trades.append(shares_to_trade)
        unhedged_option_values.append(contracts * multiplier * option_price)

    portfolio_values = np.array(portfolio_values)
    portfolio_deltas = np.array(portfolio_deltas)
    portfolio_gammas = np.array(portfolio_gammas)
    stock_trades = np.array(stock_trades)
    unhedged_option_values = np.array(unhedged_option_values)
    
    hedged_pnl = np.diff(portfolio_values)
    hedged_volatility = np.std(hedged_pnl)
    unhedged_pnl = np.diff(unhedged_option_values)
    unhedged_volatility = np.std(unhedged_pnl)
    
    hedging_effiency = 1 - hedged_volatility / unhedged_volatility
    
    mean_abs_delta = np.mean(np.abs(portfolio_deltas))
    mean_abs_gamma = np.mean(np.abs(portfolio_gammas))

    stock_turnover = np.sum(np.abs(stock_trades))
    
    return [hedged_volatility, hedging_effiency, mean_abs_delta, mean_abs_gamma, stock_turnover]
