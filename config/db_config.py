# Define the database configuration
DB_CONFIG = {
    "driver": "ODBC Driver 17 for SQL Server",
    "server": "localhost",
    # "server": "10.10.0.1"  # if the server is on another machine in the LAN
    # "server": "192.168.1.50,1435"  # if the server uses a different port
    # "server": "my-server.database.windows.net"  # for Azure SQL
    "database": "Chinook",
    "username": "user",
    "password": "dbpass#13"
}