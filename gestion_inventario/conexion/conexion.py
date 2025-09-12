import mysql.connector

def get_mysql_connection(host, user, password, database, port=3306):
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port
    )

    
