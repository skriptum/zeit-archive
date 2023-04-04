#Create Database and set up Tables
import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    """ 
    create a database connection to the SQLite database specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn
    
def create_table(conn, create_table_sql):
    """ 
    create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

if __name__ == '__main__':
    conn = create_connection("articles.db")
    
    sql_create_articles_table = """ 
    CREATE TABLE IF NOT EXISTS articles (
        id text PRIMARY KEY,
        year integer NOT NULL,
        title text NOT NULL,
        author text,
        keywords text,
        date text,
        ressort text,
        issue_id text,
        FOREIGN KEY (id) REFERENCES issues (issue_id)
        ) """
    
    sql_create_issues_table = """
    CREATE TABLE IF NOT EXISTS issues (
        id text PRIMARY KEY,
        year integer NOT NULL,
        nr_articles integer,
        accessed text NOT NULL,
        published text NOT NULL,
        ressorts text NOT NULL
        ) """
    
    create_table(conn, sql_create_articles_table)
    create_table(conn, sql_create_issues_table)
    print("Database created")
