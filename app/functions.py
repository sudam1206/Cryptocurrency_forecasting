
import pandas as pd

from urllib.parse import urlparse
from .config import db_user,db_pass,db_port,db_host,db_name
import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


import websockets


def create_tables():


    # Connect to the database
    conn = psycopg2.connect(host=db_host, dbname=db_name, user=db_user, password=db_pass, port= db_port)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historical_data (
        timestamp TIMESTAMP NOT NULL,
        open NUMERIC NOT NULL,
        high NUMERIC NOT NULL,
        low NUMERIC NOT NULL,
        close NUMERIC NOT NULL,
        volume NUMERIC NOT NULL,
        coin VARCHAR(50) NOT NULL,
        date DATE NOT NULL,
        time TIME NOT NULL,
        interval VARCHAR(50) NOT NULL,
        PRIMARY KEY (timestamp, coin, interval)
    );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS streaming_data (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP NOT NULL,
        open NUMERIC NOT NULL,
        high NUMERIC NOT NULL,
        low NUMERIC NOT NULL,
        close NUMERIC NOT NULL,
        volume NUMERIC NOT NULL,
        coin VARCHAR(50) NOT NULL,
        interval VARCHAR(50) NOT NULL
    );
    ''')

    # Commit changes and close the connection
    cursor.close()
    conn.close()




def insert_into_db(df,table_name = 'streaming_data'):

    connection = psycopg2.connect(host=db_host, dbname=db_name, user=db_user, password=db_pass, port= db_port)
    cursor = connection.cursor()
    if table_name == 'streaming_data':
        for index, row in df.iterrows():
            try:
                cursor.execute(f'''
                INSERT INTO {table_name} (timestamp, open, high, low, close, volume, coin, interval)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            ''', (row['timestamp'], row['open'], row['high'], row['low'], row['close'], row['volume'], row['coin'], row['interval']))
            except psycopg2.IntegrityError:
                connection.rollback()  # Rollback if any insertion fails due to unique constraint
            else:
                connection.commit()
    elif table_name == 'historical_data':
        for index, row in df.iterrows():
            try:
                cursor.execute('''
                INSERT INTO historical_data (timestamp, open, high, low, close, volume, coin, date, time, interval)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (row['timestamp'], row['open'], row['high'], row['low'], row['close'], row['volume'], row['coin'], row['date'], row['time'], row['interval']))
            except psycopg2.IntegrityError:
                connection.rollback()  # Rollback if any insertion fails due to unique constraint
            else:
                connection.commit()
    cursor.close()
    connection.close()



def extract_ohlcv(source):
  
  event_time = pd.to_datetime(source['data']['E'], unit='ms')
  open = source['data']['k']['o']
  high = source['data']['k']['h']
  low = source['data']['k']['l']
  close = source['data']['k']['c']
  volume = source['data']['k']['v']
  klines = source['data']['k']['i']
  coin = source['data']['s']

  data = {
      'open':open,
      'high':high,
      'low':low,
      'close':close,
      'volume':volume,
      'interval':klines,
      'coin':coin
  }

  df = pd.DataFrame(data, index=[event_time])
  df.index.name = 'timestamp'
  df[['open','high','low','close','volume']] = df[['open','high','low','close','volume']].astype(float)
  df = df.reset_index()
#   print(df)
  insert_into_db(df,'streaming_data')  # Call the insert function here

  return df

async def on_message(message):
  message = json.loads(message)
  extract_ohlcv(message)
  
async def on_error(error):
            print(error)


async def run_binance_socket(coin, kline, on_message, on_error):
    klines = 'kline_' + kline
    socket = f'wss://stream.binance.com:9443/stream?streams={coin}@{klines}'
    
    async with websockets.connect(socket) as ws:
        try:
            while True:
                message = await ws.recv()
                await on_message(message)
        except websockets.ConnectionClosedError:
            await on_error("Connection closed with error.")
        except websockets.ConnectionClosedOK:
            await on_error("Connection closed okay.")
        except Exception as e:
            await on_error(f"An error occurred: {str(e)}")

        


