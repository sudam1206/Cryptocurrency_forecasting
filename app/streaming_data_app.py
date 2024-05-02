import dash
from dash import Dash, dcc, html, Input, Output, State
import plotly.graph_objects as go
from binance import Client
import dash
import pandas as pd
from urllib.parse import urlparse
from .config import  API_KEY, API_SECRET,db_user,db_pass,db_port,db_host,db_name
from .functions import create_tables,  run_binance_socket, on_error, on_message
import threading
import asyncio
import psycopg2
import warnings

warnings.filterwarnings('ignore')





def create_streaming_data_app():
    app = dash.Dash(__name__, suppress_callback_exceptions=True, requests_pathname_prefix='/streaming_data/')

    create_tables()


    client = Client(API_KEY, API_SECRET)

    info = client.get_exchange_info()
    coins = []

    for s in info['symbols']:
        if s['symbol'].endswith('USDT'):
            coins.append(s['symbol'])
            


    app.layout = html.Div([
        html.H2("Cryptocurrency Streaming Data", style={'text-align': 'center', 'font-size': '30px'}),
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
            value='1m'
        ),
        html.Button('Start Streaming', id='submit-btn', n_clicks=0),
        dcc.Graph(id='live-graph',
                   config={'responsive':True}
                   ),
        dcc.Interval(
            id='graph-update',
            interval=2*1000,  # in milliseconds
            n_intervals=0
        ),
    ])

    @app.callback(
            Output('live-graph', 'figure'),
            [Input('submit-btn', 'n_clicks'),
             Input('graph-update', 'n_intervals')],
             [State('dropdown-coin', 'value'),
              State('dropdown-interval', 'value')]
    )
    def update_graph(n_clicks, coin, interval,n):

        klines = 'kline_' + n
        socket = f'wss://stream.binance.com:9443/stream?streams={interval.lower()}@{klines}'
        

        def start_async_loop():
            asyncio.new_event_loop().run_until_complete(
                run_binance_socket(interval.lower(), n, on_message, on_error)
                )
    
        # Start the async loop in a separate thread
        thread = threading.Thread(target=start_async_loop)
        thread.start()
        
        print(f'Running WebSocket for {interval} with kline {n}.')

        query = f"select * from streaming_data where coin = '{interval}' and interval = '{n}'  ORDER BY timestamp desc limit 200"
        
        connection = psycopg2.connect(host=db_host, dbname=db_name, user=db_user, password=db_pass, port= db_port)
        df = pd.read_sql_query(query, connection)

        connection.close()

        fig = go.Figure(go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            
        ))

        fig.update_layout(
            xaxis_title="<b>Date-Time(above) and Volume(bottom)</b>",
            yaxis_title="<b>Price in USD</b>",
            font=dict(family="Arial, sans-serif", size=12, color="RebeccaPurple")
        )
        return fig
    

    return app