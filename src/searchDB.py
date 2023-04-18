#%%
import sqlite3
from sqlite3 import Error
import numpy as np
import pandas as pd

from plotly import graph_objects as go
import plotly.express as px

#%%
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

#%%
def get_issues_df(conn):
    """
    Query all rows in the issues table
    :param conn: the Connection object
    :return: a pandas dataframe
    """
    df = pd.read_sql_query("SELECT * FROM issues", conn)
    return df


#%%
def search_by_author(conn, author):
    """
    Query all rows in the issues table
    :param conn: the Connection object
    :return: a pandas dataframe
    """
    df = pd.read_sql_query("SELECT * FROM articles WHERE author = ?", conn, params=(author,))
    return df

def search_by_keyword(conn, keyword):
    """
    Query all rows in the issues table
    :param conn: the Connection object
    :return: a pandas dataframe
    """
    df = pd.read_sql_query("SELECT * FROM articles WHERE keywords LIKE ?", conn, params=('%'+keyword+'%',))
    return df


# %%
# Plotting functions
def plot_keyword_histogram(conn, keywords):
    """
    Plot a histogram of articles per year of given keywords
    :param conn: the Connection object
    :param keyword: the keywords to search for (a list of strings)
    :return: a plotly figure
    """
    fig = go.Figure()

    if type(keywords) == str:
        keywords = [keywords,]

    for keyword in keywords:
        df = search_by_keyword(conn, keyword)

        counts, bins = np.histogram(
            df['year'], 
            bins=range(1947, 2023))
        
        bins = 0.5 * (bins[:-1] + bins[1:]) # center the bins

        fig.add_trace(
            go.Scatter(
                x=bins, 
                y=counts, 
                mode="lines", 
                name=keyword)
            )

    return fig

def plot_author_histogram(conn, author):
    """
    Plot a histogram of articles per year of a given author
    :param conn: the Connection object
    :param author: the author to search for
    :return: a plotly figure
    """

    df = search_by_author(conn, author)
    fig = px.histogram(df, x="year")

    # make bin sizes to one each year
    fig.update_traces(xbins=dict( # bins used for histogram
            start=1947,
            end=2023,
            size=1
        ))

    return fig
#%%
def get_author_keywords(conn, author):
    """
    Query all rows in the issues table
    :param conn: the Connection object
    :return: a pandas dataframe
    """
    df = pd.read_sql_query("SELECT keywords FROM articles WHERE author = ?", conn, params=(author,))
    return df

def plot_author_keywords(conn, author):
    """
    plot 10 most used keywords of author
    :param conn: the Connection object
    :param author: the author to search for
    :return: a plotly figure
    """
    df = get_author_keywords(conn, author)
    df = df['keywords'].str.split(',', expand=True).stack().value_counts()

    fig = px.bar(df[:10])
    return fig

#%%
def plot_article_histogram(conn):
    """
    Plot a histogram of articles per year
    :param conn: the Connection object
    :return: a plotly figure
    """
    df = get_issues_df(conn)
    fig = px.histogram(df, x="year", y="nr_articles")

    # make bin sizes to one each year
    fig.update_traces(xbins=dict( # bins used for histogram
            start=1947,
            end=2023,
            size=1
        ))

    return fig

#%%
if __name__ == '__main__':
    database = "../articles.db"

    # create a database connection
    conn = create_connection(database)
    
    #%%
    #Histogram of articles per year of a given keyword
    plot_keyword_histogram(conn, ["Adenauer", "Brandt", "Kohl"]).show()

    #%%
    #Histogram of articles per year of a given author
    plot_author_histogram(conn, "Thomas_Hanke").show()

    #%%
    #Plot 10 most used keywords of author
    plot_author_keywords(conn, "Thomas_Hanke").show()

    #%%
    #Histogram of articles per year
    plot_article_histogram(conn).show()


# %%


