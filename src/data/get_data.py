
from dotenv import load_dotenv
import os

import requests
from tabula import read_pdf
import pandas as pd 

import yfinance as yf
import numpy as np

def load_datapath(env_path: str = ".env") -> str:
    """Load the data path from the .env file.
    
    Parameters
    ----------
    env_path : str, optional
        Path to the .env file, by default ".env"
        
    Returns
    -------
    str
        Path to the data folder.
    """

    # get environment variables
    load_dotenv(dotenv_path=env_path)
    DATAPATH = os.getenv("DATAPATH")

    return DATAPATH

def get_BEL20_composition(data_path: str, url: str = "https://live.euronext.com/sites/default/files/documentation/index-composition/BEL_20_Index_Composition.pdf") -> list: 
    """Get tickers of stocks belonging to the BEL20 index.
    
    Parameters
    ----------
    data_path : str
        Path to the data folder.
    url : str, optional
        URL of the pdf file containing the composition of the BEL20 index, by default "https://live.euronext.com/sites/default/files/documentation/index-composition/BEL_20_Index_Composition.pdf"
        
    Returns
     -------
    list
        List of tickers of stocks belonging to the BEL20 index.
    """


    # Get data from Euronext website
    response = requests.get(url)
    
    # Write content in pdf file
    pdf = open(f"{data_path}/composition_BEL_20.pdf", 'wb')
    pdf.write(response.content)
    pdf.close()

    table = read_pdf(f"{data_path}/composition_BEL_20.pdf", pages="all", multiple_tables=False, pandas_options={'header': None})[0] # Get data from pdf
    tickers = [f"{ticker}.BR" if country=="BE" else f"{ticker}.AS" for country, ticker in zip(table[1], table[2])] # Add .BR or .AS to tickers

    return tickers

def get_data(tickers: list, data_path: str, length_of_data: str = "60d", n_lags: int = 10) -> None:
    """Get data from Yahoo Finance.
    
    Parameters
    ----------
    tickers : list
        List of tickers of stocks.
    data_path : str
        Path to the data folder.
    length_of_data : str, optional
        Length of the data to get from Yahoo Finance, by default "60d"
    n_lags : int, optional
        Number of lags to add to the data, by default 10
    
    Returns
    -------
    String with location of data.
    
    """

    # Get data from Yahoo Finance
    data = pd.DataFrame()
    for ticker in tickers: 
        msft = yf.Ticker(ticker)
        hist = msft.history(period=length_of_data)
        hist['ticker'] = ticker
        data = pd.concat([data, hist])
    
    data["close_previous_day"] = data.groupby("ticker")["Close"].shift(1) # shift the close price by 1 day
    data["close_growth"] = np.log(data["Close"]) - np.log(data["close_previous_day"]) # calculate the growth rate
    data.rename(columns={'Close': 'close'}, inplace=True) # rename the column

    for i in range(1, n_lags+1): 
        data[f"close_growth_lag_{i}"] = data.groupby("ticker")["close_growth"].shift(i) # shift the close price by i days
    
    # Write data to pickle file
    data.filter(regex='ticker|Date|close').to_pickle(f"{data_path}/BEL_20.pkl")  # filter columns and write to pickle file

    return f"{data_path}/BEL_20.pkl"