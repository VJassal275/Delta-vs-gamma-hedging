# Delta_vs_delta-gamma-hedging

Comparison of delta and delta-gamma hedging algorithms to hedge 10 European call option contracts

## Model

The aim of this project was to compare the metrics of portfolio P&L volatility, hedging efficiency, mean absolute delta and gamma and stock turnover, in order to investigate whether neutralising second-order price exposure through gamma hedging improves hedge stability relative to standard Delta hedging, and to quantify the additional trading required.

Portfolio delta is calculated as:

$$\Delta_P = N_O M \Delta_O + S $$

for option delta $$\Delta_O$$, multiplier $$M$$, $$N_O$$ option contracts, and stock position $$S$$.

When portfolio delta exceeds the specified tolerance:

$$|\Delta_P| > \epsilon_\Delta$$

the stock position is adjusted toward delta neutrality through rounding the portfolio delta to the nearest integer and shorting that number of stocks (if the number is negative the stocks are bought).

Using a second option to hedge gamma with, the portfolio gamma is calculated as 

$$\Gamma_P = N_O M \Gamma_O + N_H M \Gamma_H $$

where $$N_H$$ represents the number of contracts of the second option with respective gamma $$\Gamma_H$$.

If gamma exceeded its specified tolerance:

$$|\Gamma_P| > \epsilon_\Gamma$$

then the number of second option contracts to buy was calculated by 

$$n = -\text{round}\left(\frac{\Gamma_P}{\Gamma_H} \right)$$

rounded to the nearest integer (selling options if this number is negative). After this the portfolio delta is now at 

$$\Delta_P = N_O M \Delta_O + N_H M \Delta_H + S $$

and the portfolio is delta-hedged the same as before.


The performance metrics of this project were:

P&L volatility - the standard deviation of daily hedged portfolio P&L

Hedging efficiency - calculated as below:

$$ \text{HE} = 1 - \frac{\sigma_{hedged P\&L}}{\sigma_{unhedged P\&L}} $$

Higher values indicate a greater reduction in P&L volatility.

Mean absolute delta: average residual first-order underlying exposure

Mean absolute gamma: average residual second-order exposure

Stock turnover: total absolute number of shares traded

## Assumptions and limitations

This project made assumptions in all areas from obtaining data to the hedging process.

Firstly, historical data was obtained from python library yfinance. This data only included closing prices and no info about options available at the time or any implied volatility. Thus, the 10-day rolling realised volatility was used to estimate the implied volatility and options were priced with their Black-Scholes price. 

Additionally, in order to gamma hedge, a synthetic option market was created with puts and calls of strike prices at 0.8, 0.9, 1.0, 1.1 and 1.2 times the stock price. The time to expiration was taken to be the same expiry date as the original call option contracts. 

This project also assumed zero transaction costs due to past bid and ask as well as volume data not present. Furthermore this also assumed no dividends or arbitrage and a constant risk-free rate. All trades were done with whole stock shares.

The delta and gamma tolerances were chosen to be 10% the absolute initial delta and gamma values as an arbitrary threshold

## Example output



## Build and run

## Results

## Conclusion
