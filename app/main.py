from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
import dash
from dash import Dash,html,dcc
from .historical_data_app import create_historical_data_app
from .streaming_data_app import create_streaming_data_app

from sqlalchemy import create_engine
import pandas as pd
import psycopg2


DATABASE_URL = 'postgresql+psycopg2://myuser:mypassword@db:5432/mydatabase'

engine = create_engine(DATABASE_URL)
connection = engine.connect()









app = FastAPI(title="FastAPI, Docker, and Dash")

historical_data_dash_app = create_historical_data_app()
app.mount("/historical_data", WSGIMiddleware(historical_data_dash_app.server))





@app.get("/")
def read_root():
    return {"hello": "Welcome to my app",
            "link to historical data dashboard":"http://localhost:8008/historical_data/",
            "link to streaming data dashboard": "http://localhost:8008/streaming_data/"}

streaming_data_dash_app = create_streaming_data_app()
app.mount("/streaming_data", WSGIMiddleware(streaming_data_dash_app.server))
