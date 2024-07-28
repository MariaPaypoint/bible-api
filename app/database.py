# database.py
import mysql.connector
from mysql.connector import Error

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="bmysql",
            user="root",
            password="XSNx0evIpDBXUPSthhHq",
            database="bible_pause",
			port="3306"
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection
	