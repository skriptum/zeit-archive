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

def create_articles_table(conn):
    """
    create a table from the create_table_sql statement
    :param conn: Connection object
    """
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
    create_table(conn, sql_create_articles_table)

def create_issues_table(conn):
    """
    create a table from the create_table_sql statement
    :param conn: Connection object
    """
    sql_create_issues_table = """
    CREATE TABLE IF NOT EXISTS issues (
        id text PRIMARY KEY,
        year integer NOT NULL,
        nr_articles integer,
        accessed text NOT NULL,
        published text NOT NULL,
        ressorts text NOT NULL
        ) """
    create_table(conn, sql_create_issues_table)

if __name__ == '__main__':
    conn = create_connection("articles.db")
    
    if conn is not None:
        create_articles_table(conn)
        create_issues_table(conn)
    else:
        print("Error! cannot create the database connection.")
    print("Database created")
