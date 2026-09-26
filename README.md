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

These values were compared between the two strategies with paired t-tests 

## Assumptions and limitations

This project made assumptions in all areas from obtaining data to the hedging process.

Firstly, historical data was obtained from python library yfinance. This data only included closing prices and no info about options available at the time or any implied volatility. Thus, the 10-day rolling realised volatility was used to estimate the implied volatility and options were priced with their Black-Scholes price. 

Additionally, in order to gamma hedge, a synthetic option market was created with puts and calls of strike prices at 0.8, 0.9, 1.0, 1.1 and 1.2 times the stock price. The time to expiration was taken to be the same expiry date as the original call option contracts. The option chosen was the one that minimised the portfolio after the initial gamma hedge (the ATM call option was excluded to avoid this degenerate case)

This project also assumed zero transaction costs due to past bid and ask as well as volume data not present. Furthermore this also assumed no dividends or arbitrage and a constant risk-free rate. All trades were done with whole stock shares.

The delta and gamma tolerances were chosen to be 10% the absolute initial delta and gamma values as an arbitrary threshold

## Example output

Output for 10 30-day SHEL options from March 24 2018 to April 23 2018:

| Metric             | Delta Hedge | Delta-Gamma Hedge |
| ------------------ | ----------: | ----------------: |
| P&L volatility     |      £42.81 |            £25.17 |
| Hedging efficiency |      55.57% |            73.88% |
| Mean $$\Delta$$    |       21.46 |             13.72 |
| Mean $$\Gamma$$    |       78.32 |              2.84 |
| Stock turnover     |         684 |               421 |
| Option turnover    |           0 |                19 |


## Build and run

### Requirements

The project uses Python 3.14 and the following packages:

* NumPy
* Pandas
* SciPy
* yfinance

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd <your-repository-name>
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` file should contain:

```text
numpy
pandas
scipy
yfinance
```

Alternatively, install the packages directly:

```bash
python3 -m pip install numpy pandas scipy yfinance
```

### 4. Run the backtest

Run the Delta hedging strategy:

```bash
python3 delta_hedging.py
```

Run the Delta-Gamma hedging strategy:

```bash
python3 delta_gamma_hedging.py
```

The programs download historical underlying price data using `yfinance`, generate the synthetic option market, run the hedging simulation, and output the performance metrics to the terminal.

### 5. Reproducing the results

The main model parameters are defined near the beginning of each script, including:

```python
ticker = "SHEL"
r = 0.02
contracts = 10
multiplier = 100
```

### Troubleshooting

On macOS, the Python executable may be `python3` rather than `python`. Check the installed version with:

```bash
python3 --version
```

If a package cannot be imported, install it using the same Python interpreter:

```bash
python3 -m pip install <package>
```

The project uses synthetic options rather than historical option-chain data, so the backtest only requires historical underlying price data from `yfinance`.


## Results

## Conclusion
