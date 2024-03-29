#%% #Importe
import requests
from datetime import datetime
import json
import os

from tqdm import tqdm #for progress bar

from bs4 import BeautifulSoup
from goose3 import Goose
from goose3.configuration import Configuration

import sqlite3
from sqlite3 import Error

from loadSelenium import *
# get_article_html()
# get_ausgabe_html()
# start_selenium()


#%%
def get_ausgabe(driver, year, issue):
    """
    Extracts the HTML from the index page
    Args: year and issue of the index page
    Returns: HTML data
    """
    issue = str(issue).rjust(2, "0") #for zeros next to numbers < 10
    index_url = f"https://www.zeit.de/{year}/{issue}/index"

    headers = {'User-Agent': 'googlebot'}
    # pretending to be the google crawler for cicumventing cookie banner and paywall

    page = requests.get(index_url, headers)

    if page.status_code == 404:
        raise Exception
    
    html = get_article_html(driver, index_url)

    return html

def get_ausgabe_links(data):
    """
    Extracts the ressorts from the index page
    Args: HTML data from the index page
    Returns: Dict with links as keys and ressort as values
    """
    soup = BeautifulSoup(data, features="lxml") # "Buchstabensuppe" definieren
    ressorts = soup.find_all("h2", class_="cp-area__headline")
    
    article_links = {}
    for r in ressorts:
        ressort_title = r.text
    
        header_articles = r.parent.find_all(class_="teaser-large__heading-link")
        small_articles = r.parent.find_all(class_="teaser-small__heading-link")
        articles = header_articles + small_articles

        for article in articles:
            article_links[article["href"]] = ressort_title
            # create a dictionary with the ressorts as keys and the links as values
        
    return article_links
        
#%%
def get_article(g, url, driver):
    """
    Extracts the metadata and the text from the article
    Args: Goose object, url of the article
    Returns: Dictionary with the metadata and the text
        with the keys: "desc", "keywords", "title", "author", "date", "article_text", "url"
    """
    
    art = get_article_data(g, url, driver)
    metadata = get_article_metadata(art)
    article_data = get_article_text(art, metadata["author"])

    # extract the comments, if there are any
    try:
        article_comments = get_article_comments(art)
    except:
        article_comments = None

    data = metadata
    data["article_text"] = article_data["text"]
    data["author"] = article_data["author"]
    data["comments"] = article_comments
    data["url"] = url

    return data

def get_article_data(g, url, driver):
    """
    Extracts the article data from the url
    Args: Goose object, url of the article
    Returns: Article object from Goose
    """

    if requests.get(f"{url}/komplettansicht").status_code == 404:
        url = url 
    else:
        url = f"{url}/komplettansicht"

    html = get_article_html(driver, url)
    art = g.extract(raw_html=html)
    return art

def get_article_metadata(art):
    """
    Extracts the metadata from the article object
    Args: Article object from Goose
    Returns: Dictionary with the metadata
    """
    title = art.title
    desc = art.meta_description
    keywords = art.meta_keywords.split(", ") #list

    image_url = art.opengraph["image"] 
    if "fallback-image" in image_url: #if there is no image, the url is a fallback image
        image_url = None 

    #example author link: 'https://www.zeit.de/autoren/R/Sabine_Rueckert/index.xml'
    try:
        author = art.opengraph["article:author"].split("/")[5]
    except:
        author = None

    # example publish date: '2017-05-23T03:56:37+02:00'
    try:
        date = art.opengraph["publish_date"]
        date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z") # automatically recognize date format
        date = date.isoformat() #convert to iso format
    except:
        date=None
    
    return {
        "title": title,
        "desc":desc,
        "keywords": keywords,
        "author": author,
        "date": date,
    }

def get_article_text(art, author=None):
    """
    Extracts the text from the article html
    Args: Article object from Goose, author name
    Returns: Dictionary with the text and the author
    """
    art_html = art.raw_html
    soup = BeautifulSoup(art_html, features="lxml")
    paragraphs = soup.find_all("p", class_="paragraph article__item") #the paragraphs of the article

    article_text = ""
    for p in paragraphs:
        text = p.text

        # cleanings
        text = text.replace("\xa0", " ") #replace non-breaking space with normal space
        text = text.replace("\u200b", "") #remove zero-width space
        text = text.replace("\u2009", "") #remove thin space
        text = text.replace("\u2002", "") #remove en space
        text = text.replace("\u2003", "") #remove em space
        text = text.replace("\u2004", "") #remove three-per-em space
        text = text.replace("\u2005", "") #remove four-per-em space
        text = text.replace("\u2006", "") #remove six-per-em space
        text = text.replace("\u2007", "") #remove figure space

        #filter out varius paragraphs that do not belong to the article
        if "zeit.de/audio" in text:
            #Audio links at the end of the article
            continue
        elif "Dieser Text ist Teil des" in text:
            # Information about ARCHIV
            continue
        elif "Die Nutzung ist" in text: 
            # Nutzungshinweis
            continue 
            
        article_text += text
    
    if author==None:
        try:
            #if no author is given, try to extract it from the text
            person = soup.find("span", itemscope="", itemtype="http://schema.org/Person")
            author = person.find("span", itemprop="name").text.replace(" ", "_") #check if person is the author
        except:
            author = None
    
    return {"text":article_text, "author":author}

def get_article_comments(art):
    """
    Extracts the comments from the article
    Args: Article object from Goose
    Returns: List of dictionaries with the comment text and metadata about user
        with keys: "comment_text", "user_name", "user_id"
    """

    soup = BeautifulSoup(art.raw_html, features="lxml")
    url = art.final_url

    #find out how many comment pages there are on this article
    pager = soup.find("nav", class_="pager")
    pages = pager.attrs["data-ct-row"]
    pages = int(pages.split("_")[-1])

    #get the comments from each page of comments
    comments_data = list()
    headers = {'User-Agent': 'googlebot'}

    #each comment page with ~4 comments
    for p in range(1, pages+1):
        html_comments = requests.get(f"{url}?page={p}#comments", headers)
        comments_soup = BeautifulSoup(html_comments.text, features="lxml")

        comments = comments_soup.select("article.comment.js-comment-toplevel")

        #each comment on the page
        for comment in comments:
            comment_text = comment.find("div", class_="comment__body").text.replace("\n", "")

            meta_infos = comment.find("div", class_="comment-meta")

            try:
                user_name = meta_infos.h4.a.text
                user_id = meta_infos.find(class_="comment-meta__name").a["href"].split("/")[-1] 
                # example profile link: https://profile.zeit.de/3954535

            except: #if name has no underlying link / profile link is not available
                user_name = meta_infos.h4.text
                user_id = None
            
            #clean and append the data
            user_name = user_name.replace("\n", "").strip()
            comments_data.append({"comment_text":comment_text, "user_name":user_name, "user_id":user_id})

    return comments_data

# %%
def get_issue(g, conn, year, ausgabe, driver):
    """
    Extracts the data from the index page
    Args: Goose object, SQL Connection, year and issue of the index page
    Returns: Metadata about Issue, List of article dictionarys
    """
    try:
        index_data = get_ausgabe(driver, year, issue=ausgabe) #TODO
        links_data = get_ausgabe_links(index_data) 
        links = links_data.keys()
    except:
        print(f"Error in {year}/{ausgabe}")
        raise Exception


    articles = list()
    for i, link in enumerate(tqdm(links)):
        try:
            art_data = get_article(g, link, driver)
        except:
            print(f"Error in {link}")
            continue

        #add id data to the dictionary
        art_data["id"] = f"{year}/{ausgabe}/{i}"
        art_data["ressort"] = links_data[link] #look up ressort in original dict

        insert_article(conn, art_data) #insert into DB

        articles.append(art_data)

    metadata ={
        "issue_id": f"{year}/{ausgabe}",
        "year": year,
        "nr_articles": len(articles),
        "ressorts": ";".join(set(links_data.values())), #get unique ressorts
        "accessed": datetime.now().isoformat(),
        "published": datetime.strptime(f"{year} {ausgabe} 4", "%Y %W %w").isoformat()
    }

    
    return metadata, articles

def get_year_data(g,conn, year, driver):
    """
    Extracts the data from all issues of a year
    Args: Goose object, SQL connection, year
    Returns: Saves the data as json file for each issue
    """
    #create year folder if it does not exist
    if not os.path.exists(f"../data/{year}"):
        os.makedirs(f"../data/{year}")

    for ausgabe in range(1,53):
        try:
            # Check if issue is already in DB
            if check_issue(conn, year, ausgabe):
                print(f"Skipping {year}/{ausgabe}")
                continue
            print(f"Downloading {year}/{ausgabe}")
            metadata, articles = get_issue(g,conn, year, ausgabe, driver)

        except:
            if not ausgabe == 53:
                print(f"Fetch Error in {year}/{ausgabe}")
                with open("../data/error_log.txt", "a") as f:
                    f.write(f"{year}:{ausgabe}\n")
            continue

        # save the data as json file
        # overwrites existing file!
        with open(f'../data/{year}/{year}_{ausgabe}.json', 'w+', encoding='utf-8') as f:
            comb_data = dict()
            comb_data["metadata"] = metadata
            comb_data["articles"] = articles

            json.dump(comb_data, f, ensure_ascii=False, indent=4)
        
        # save issue in DB
        insert_issue(conn, metadata)
    
        # save the progress    
        with open("../data/progress.txt", "a") as f:
            f.write(f"{year}:{ausgabe}\n")

#%%
def get_connection(db_file="articles.db"):
    """
    Connects to the SQLITE database
    Returns: Connection object
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

#%%
def insert_article(conn, article):
    """
    Inserts the article data into the database
    Args: Connection object, article dictionary
    """
    sql = ''' INSERT INTO articles(id,year,title,author,keywords,date,ressort,issue_id)
              VALUES(?,?,?,?,?,?,?,?) '''

    
    art = list()

    art.append(article["id"])
    art.append(int(article["id"].split("/")[0])) #split id and get year
    art.append(article["title"])
    art.append(article["author"])
    art.append(";".join(article["keywords"])) #join keywords to string seperated by ;
    art.append(article["date"])
    art.append(article["ressort"])
    art.append(f"{art[1]}/{article['id'].split('/')[1]}") #get issue id from article id

    cur = conn.cursor()
   
    cur.execute(sql, art)
    conn.commit()

def insert_issue(conn, issue):
    """
    Inserts the issue data into the database
    Args: Connection object, issue dictionary
    """
    sql = ''' INSERT INTO issues(id,year,nr_articles,ressorts,accessed,published)
              VALUES(?,?,?,?,?,?) '''

    cur = conn.cursor()
    cur.execute(sql, list(issue.values()))
    conn.commit()

def check_issue(conn, year, ausgabe):
    """
    Checks if issue is already in the database
    Args: Connection object, issue dictionary
    Returns: True if issue is in DB, False if not
    """
    sql = ''' SELECT * FROM issues WHERE id=? '''

    cur = conn.cursor()
    cur.execute(sql, (f"{year}/{ausgabe}",))
    res = cur.fetchone()

    if res:
        return True
    else:
        return False
#%%
if __name__ == "__main__":
    config = Configuration()
    config.browser_user_agent = 'googlebot'  # set the browser agent string as google crawler

    conn = get_connection()

    username = "REDACTED"
    password = "REDACTED"
    driver = start_selenium(username, password)

    with Goose(config) as g:

        current_year = datetime.now().year
        #get_year_data(g,conn, 1950)
        for year in range(2023,2024):

            print(f"Year: {year}")
            get_year_data(g,conn, year, driver)

    driver.close()
# %%
