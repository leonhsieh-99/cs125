from recipe_scrapers import scrape_me
import re
import json
import time
import requests
from collections import defaultdict
from urllib.parse import urlparse
from bs4 import BeautifulSoup as bs
import lxml
import nltk

url_set = set() # for number 1
politeness = .3
websites = ["https://allrecipes.com/"]
patterns = [r"https://www.allrecipes.*"]
pattern1 = r'^.*\\recipe\\.*$'

def get_nutrients(url):
    d = dict()
    
    return d

def scraper(url, resp):
    global url_set

    url_set.add(url) # include unique urls
    new_links = []
    items = resp.links()
    for item in items:
        for k, v in item.items():
            if k == 'href':
                new_links.append(v)
    links = extract_next_links(url, new_links)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, links):
    l = list()
    global url_set

    for link in links:
        try:
            pattern = r'(.*)\/.*\d+'
            similar_url_check = re.match(pattern, url)[1]
            comparison = re.match(pattern, new_link)[1]
            if similar_url_check != "" and similar_url_check == comparison:
                continue
        except:
            pass

        if(link not in url_set):
            l.append(link)
            url_set.add(link)
    return l

def is_valid(url):
    parsed = urlparse(url)
    try:
        for pattern in patterns:
            if re.match(pattern, url) == None:
                return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())


        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise

    return

def main():
    global websites
    for website in websites:
        print(website)
        try:
            resp = scrape_me(website)
        except:
            print(website)
        new_websites = scraper(website, resp)
        websites.extend(new_websites)
        if resp.title() != "":
            print(resp.title())
            print(resp.nutrients())
        time.sleep(politeness)

if __name__ == "__main__":
    main()