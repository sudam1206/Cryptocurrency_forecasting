
from urllib.parse import urlparse





# Database configuration
DATABASE_URL = "postgresql+psycopg2://myuser:mypassword@db:5432/mydatabase"


def get_db_config(url):
    result = urlparse(url)
    return {
        "username": result.username,
        "password": result.password,
        "database": result.path[1:],  # Remove leading '/'
        "hostname": result.hostname,
        "port": result.port
    }




DB_CONFIG = get_db_config(DATABASE_URL)

db_user = DB_CONFIG['username']
db_pass = DB_CONFIG['password']
db_name = DB_CONFIG['database']
db_host = DB_CONFIG['hostname']
db_port = DB_CONFIG['port']



# API configuration
API_KEY = 'OCFFTpMXW1I2LJo7r2XVfvda5g80zpfbrXTvbRGI8JvQSe9LyVmpeuMz52sSo6q9'
API_SECRET = 'a2kaw1nh7tsbe1NzV0tXn38knlbwTkECFOApjZ5pcMYP6igPNPUqQJ8mFRms0TcS'