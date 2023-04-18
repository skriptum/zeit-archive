# Description: Classify the text of the articles using the spacytextblob library
# Save the Text Data and the Classification into the Database in the TEXT table
#%%
import sqlite3
from sqlite3 import Error

import json
import os

import spacy
from spacytextblob.spacytextblob import SpacyTextBlob

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
def insert_article(conn, article_text, article_id, polarity, subjectivity):
    """
    Create a new article in the TEXT table
    :param conn:
    :param article_text:    text of the article
    :param article_id:      id of the article
    :param polarity:        polarity of the article
    :param subjectivity:    subjectivity of the article
    """
    sql = ''' INSERT INTO TEXT(id, text, polarity, subjectivity)
                VALUES(?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (article_text, article_id, polarity, subjectivity))
    conn.commit()
    


#%%
def classify_article(nlp, article_text):
    """
    Classify the article
    :param article_text:    text of the article
    :return:                classification
    """
    doc = nlp(article_text)

    return doc._.blob.polarity, doc._.blob.subjectivity
#%%
if __name__ == '__main__':
    print("setting up spacy")
    nlp = spacy.load('de_core_news_sm')
    nlp.add_pipe('spacytextblob')

    print("setting up database connection")
    conn = create_connection("../articles.db")
    path = "../data/"

    #%%
    # walk through all files in the data folder
    for dirpath, dirnames, filenames in os.walk(path):
        print("walking through files")

        for filename in [f for f in filenames if f.endswith(".json")]:
            filepath = os.path.join(dirpath, filename)

            with open(filepath, "r") as f:
                # load the json file
                data = json.load(f)

                # get the articles
                for article in data["articles"]:
                    # classify the article
                    polarity, subjectivity = classify_article(nlp, article["article_text"])

                    # insert the article into the database
                    insert_article(
                        conn,  
                        article["id"], 
                        article["article_text"],
                        polarity=polarity, 
                        subjectivity=subjectivity
                        )
