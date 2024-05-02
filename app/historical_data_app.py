import dash
from dash import Dash, dcc, html, Input, Output, State
import plotly.graph_objects as go
from binance import Client
import dash
import pandas as pd
from datetime import datetime, timedelta
from urllib.parse import urlparse
from .config import  API_KEY, API_SECRET
from .functions import create_tables, insert_into_db





def GetHistoricalData(coin,howLong,klines = Client.KLINE_INTERVAL_5MINUTE ):
    
    client = Client(API_KEY, API_SECRET)

    # Calculate the timestamps for the binance api function
    untilThisDate = datetime.now()
    sinceThisDate = untilThisDate - timedelta(days = int(howLong))
    # Execute the query from binance - timestamps must be converted to strings !
    candle = client.get_historical_klines(coin, klines, str(sinceThisDate), str(untilThisDate))

   # Create a dataframe to label all the columns returned by binance so we work with them later.
    df = pd.DataFrame(candle, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'])
    # as timestamp is returned in ms, let us convert this back to proper timestamps.
    df.timestamp = pd.to_datetime(df.timestamp, unit='ms')#.dt.strftime("%Y-%m-%d %H-%M-%S")
    # df.set_index('dateTime', inplace=True)
    df['coin'] = coin
    df['date'] = df['timestamp'].dt.date
    df['time'] = df['timestamp'].dt.time
    df['interval']= klines

    # Get rid of columns we do not need
    df = df.drop(['closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol','takerBuyQuoteVol', 'ignore'], axis=1)

    return(df)


def create_historical_data_app():
    app = dash.Dash(__name__, suppress_callback_exceptions=True, requests_pathname_prefix='/historical_data/')

    create_tables()


    client = Client(API_KEY, API_SECRET)

    info = client.get_exchange_info()
    coins = []

    for s in info['symbols']:
        if s['symbol'].endswith('USDT'):
            coins.append(s['symbol'])
            # print(s['symbol'])


    app.layout = html.Div([
        html.H2("Cryptocurrency Historical Data", style={'text-align': 'center', 'font-size': '30px'}),
        html.Label("Select Coin:", style={'font-weight': 'bold'}),
        dcc.Dropdown(
            id='dropdown-coin',
            options=[{'label': coin, 'value': coin} for coin in coins],
            value='BTCUSDT'
        ),
        html.Label("Select Interval for Klines:", style={'font-weight': 'bold'}),
        dcc.Dropdown(
            id='dropdown-interval',
            options=[{'label': interval, 'value': interval} for interval in ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']],
            value='5m'
        ),
        html.Label("Select Duration:", style={'font-weight': 'bold'}),
        dcc.Dropdown(
            id='dropdown-duration',
            options=[{'label': str(i), 'value': i} for i in range(1, 6)],
            value=1
        ),
        html.Button('Submit', id='submit-btn', n_clicks=0),
        dcc.Graph(id='graph'),
        html.Button("Download JSON", id="btn_json"),
        dcc.Download(id="download-dataframe-json"),
    ])

    @app.callback(
        Output('graph', 'figure'),
        Input('submit-btn', 'n_clicks'),
        [State('dropdown-coin', 'value'),
         State('dropdown-interval', 'value'),
         State('dropdown-duration', 'value')]
    )
    def update_graph(n_clicks, coin, interval, duration):
        
        global df
        df = GetHistoricalData(coin, duration, interval)
        table_name = 'historical_data'
        insert_into_db(df, table_name)
        fig = go.Figure(go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        ))
        fig.update_layout(
            xaxis_title="<b>Date-Time(above) and Volume(bottom)</b>",
            yaxis_title="<b>Price in USD</b>",
            font=dict(family="Arial, sans-serif", size=12, color="RebeccaPurple")
        )
        return fig
    
    @app.callback(
        Output("download-dataframe-json", "data"),
        Input("btn_json", "n_clicks"),
        prevent_initial_call=True,
    )
    def func(n_clicks):
        return dcc.send_data_frame(df.to_json, "mydf.json")


    return app