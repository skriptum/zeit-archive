#%%
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import time
#%%
def start_selenium(username, password):
    """
    Start the Selenium driver
    """
    driver = webdriver.Firefox()
    driver.get("https://meine.zeit.de/anmelden")

    # Login Page
    driver.find_element(By.ID ,"login_email").send_keys(username)
    driver.find_element(By.ID ,"login_pass").send_keys(password)
    driver.find_element(By.ID ,"login_pass").send_keys(Keys.ENTER)

    time.sleep(5)
    # Cookies Page
    driver.find_element(By.ID, "sp_message_container_804280").click()

    return driver

#%%

def get_ausgabe_html(driver, url):
    """
    Use Selenium to get the Ausgabe HTML from the ZEIT Archiv
    """
    driver.get(url)
    html = driver.page_source

    return html
 
#%%
def get_article_html(driver, url):
    """
    Use Selenium to get the article HTML
    """
    driver.get(url)
    html = driver.page_source

    return html

# %%
