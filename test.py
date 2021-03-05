from recipe_scrapers import scrape_me
import re
import requests
import lxml
import nltk
import json
from bs4 import BeautifulSoup as bs
from nltk.tokenize import RegexpTokenizer
# give the url as a string, it can be url from any site listed below

def main():
    '''
    scraper = scrape_me('https://www.therecipedepository.com/recipe/1583/cheesey-broccoli-bake')
    print(scraper.title())
    print(scraper.total_time())
    print(scraper.yields())
    print(scraper.ingredients())
    print(scraper.instructions())
    print(scraper.image())
    print(scraper.host())
    #print(scraper.links())
    print(scraper.nutrients())  # if available)

    scraper = scrape_me('https://www.allrecipes.com/recipe/19037/dessert-crepes/#nutrients')
    print(scraper.title())
    print(scraper.verbose_name=''utrients()) 
    '''
    resp = requests.get("https://www.allrecipes.com/")
    soup = bs(resp.text, 'lxml')
    for link in soup.find_all('a'):
        if not link.has_attr('href'):
            continue
        print(link)
    #print(resp.text)

    #print(soup.text)
    '''
    s = str(soup.head.script)
    print(s)
    #print(soup.head.script)
    ind1 = s.find('\n')
    ind2 = s.rfind('\n')
    info = json.loads(s[s.find('\n')+1:s.rfind('\n')])[1]
    print(info['name'])
    print(info['description'])
    print(info['recipeYield'])
    print(info['recipeIngredient'])
    print(info['totalTime'])
    print(info['nutrition'])
    print(info['image'])
    print(info['recipeInstructions'])
    print(info['recipeCategory'])
    print(info['recipeCuisine'])
    pattern = r'(\w+)(?:Content)'
    new_d = dict()
    for k, v in info['nutrition'].items():
        if k == '@type':
            continue
        if k == 'calories':
            new_d[k] = v
            continue
        obj = re.match(pattern, k)
        try:
            new_d[obj[1]] = v
        except:
            continue
    print(new_d)
    # parse and tokenize here
    tokenizer = RegexpTokenizer(r"[0-9a-zA-Z']+")
    tokens = tokenizer.tokenize(soup.get_text())
    #print(tokens)
    #'''

if __name__ == "__main__":
    main()