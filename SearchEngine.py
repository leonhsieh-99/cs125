import json
import re
import os
import numpy as np
from bs4 import BeautifulSoup as bs
from nltk.stem import PorterStemmer
from collections import defaultdict
from nltk.tokenize import RegexpTokenizer
from collections import Counter
from nltk.corpus import stopwords
import pickle
import time
import sys
hashseed = os.getenv('PYTHONHASHSEED')
if not hashseed:
    os.environ['PYTHONHASHSEED'] = '0'
    os.execv(sys.executable, [sys.executable] + sys.argv)

def sim_hashfn(word):
    return '{:064b}'.format(hash(word)+sys.maxsize+1)

def delete_partitions():
    for file in os.listdir(os.getcwd()):
        if re.match(r'^P\d\.json$', file):
            os.remove(file)
    try:
        os.remove("temp1.json")
    except:
        pass
    try:
        os.remove("temp2.json")
    except:
        pass

def merge_partitions():
    files = []
    for file in os.listdir(os.getcwd()):
        if re.match(r'^P\d\.json$', file):
            files.append(file)
    for i in range(len(files)-1):
        if i == len(files) - 2:
            print("last file")
            f = open("merge_index.json", 'w')
        elif i%2 == 1:
            if i > 2:
                os.remove("temp1.json")
            f = open("temp1.json", 'w')
        elif i%2 == 0:
            if i > 2:
                os.remove("temp2.json")
            f = open("temp2.json", 'w')
        f1 = open(files[i])
        f2 = open(files[i+1])
        line1 = f1.readline()
        line2 = f2.readline()
        while(line1 != "" or line2 != ""):
            jsonObj1 = {"~~~": ""} if line1 == "" else json.loads(line1) # highest ASCII val
            jsonObj2 = {"~~~": ""} if line2 == "" else json.loads(line2) # highest ASCII val
            key1, key2 = list(jsonObj1.keys())[0], list(jsonObj2.keys())[0]
            if key1 == key2:
                jsonObj1[key1].update(jsonObj2[key2])
                updated_posting = jsonObj1
                line1 = f1.readline()
                line2 = f2.readline()
            elif key1 < key2:
                updated_posting = {key1:jsonObj1[key1]}
                line1 = f1.readline()
            elif key1 > key2:
                updated_posting = {key2:jsonObj2[key2]}
                line2 = f2.readline()
            else:
                print(f"key1: {key1}\tkey2: {key2}")
                raise Exception("Error error error")
            json.dump(updated_posting, f)
            f.write("\n")
        f1.close()
        f2.close()
        f.close()
        if i%2 == 1:
            files[i+1] = "temp1.json"
        elif i%2 == 0:
            files[i+1] = "temp2.json"

'''
-makes the inverted index
-For the sake of my computer's well being, the index is partitioned off into
    4 pieces and is later merged.
'''
def makeIndex():
    ID = 0
    ID_url_dict = dict()
    doc_count = 56000
    doc_counter = 0 #used for the partial indexes
    titles_set = defaultdict(set)
    headings_set = defaultdict(set)
    bold_set = defaultdict(set)
    important_sets = [titles_set, bold_set, headings_set]
    partitions = 4
    num_partitions = 1
    ps = PorterStemmer()
    tokenizer = RegexpTokenizer(r"[a-zA-Z0-9']+")
    inverted_index = dict()
    #simhash_dict = dict()

    for directory in os.listdir(os.getcwd() + "\\DEV"):
        path = os.getcwd() + "\\DEV\\" + directory
        try:
            os.listdir(path)
        except:
            continue
        for file in os.listdir(path):
            with open(path + '\\' + file) as f:
                data = json.loads(f.read())
            soup = bs(data['content'], 'lxml') # parse using bs and lxml
            #simhash_file = list() # contains all the hashed words of the documentuih
            try:
                body = soup.body.get_text()
            except:
                body = ""
            words = tokenizer.tokenize(body) # tokenize the body
            for w in words: # stemming
                word = ps.stem(w.lower().rstrip())
                #simhash_file.append(sim_hashfn(word))
                try:
                    inverted_index[word][ID] += 1
                except KeyError:
                    try:
                        inverted_index[word].update({ID:1})
                    except KeyError:
                        inverted_index[word] = {ID:1}

            titles = soup.find_all('title') # find all title tags
            bolds = soup.find_all(re.compile(r'.*^(?:b|strong)$')) # find all bold tags
            headers = soup.find_all(re.compile('^h[1-6]$')) # find all heading tags
            # tokenize all the important/title words
            important_words = [titles, bolds, headers]
            for i in range(3):
                if important_words[i] == None:
                    continue
                for important_word in important_words[i]:
                    if important_word.string == None:
                        continue
                    for word in tokenizer.tokenize(important_word.string):
                        w = ps.stem(word.lower().rstrip())
                        important_sets[i][ID].add(w)

            # partial index dump (STILL IN THE WORKS)
            if doc_counter > doc_count/partitions:
                inverted_index = {k:v for k, v in sorted(inverted_index.items())}
                with open(f"P{num_partitions}.json", 'w') as f:
                    for k, v in inverted_index.items():
                        json.dump({k: v}, f)
                        f.write('\n')
                inverted_index.clear()
                num_partitions += 1
                doc_counter = 0
            ID_url_dict[ID] = data['url']
            #simhash_dict.update({ID:simhash_file})
            ID += 1
            doc_counter += 1
            print(ID)
    inverted_index = {k:v for k, v in sorted(inverted_index.items())}
    with open(f"P{num_partitions}.json", 'w') as f:
        for k, v in inverted_index.items():
            json.dump({k: v}, f)
            f.write('\n')
    inverted_index.clear()

    with open("info.p", 'wb') as f: # save these informations for later
        pickle.dump((ID_url_dict,important_sets) , f)

    print("done serializing\n")

'''
1. goes through index line by line (we assume it's sorted here)
2. calculates the tf-idf while taking the important words into account
3. writes the {word: tf-idf} into a file and the {word: <file pointer -> tf-idf entry>} into another
4. also creates and writes simhash into a file
'''
def calculate_helpers():
    with open("info.p", 'rb') as f:
        info = pickle.load(f)
    urls = info[0] # dict: ID --> url
    important_sets = info[1] # list of dict(set)

    N = len(urls)
    simhash_dict = {}
    f1 = open("merge_index.json")
    f2 = open("tf_idf.json", 'w')
    f3 = open("fp.json", 'w')
    for jsonObj in f1:
        obj = json.loads(jsonObj)
        for word, postings in obj.items():
            tf_idf = {} # will be dumping this every iteration for the sake of my poor RAM
            for docID, appearances in postings.items():
                # weighing based on important words
                scale = 1
                for i in range(3):
                    try:
                        if word in important_sets[i][docID]:
                            if i == 0: # is a title
                                scale *= 1.5
                            elif i == 1: # is a bold
                                scale *= 1.1
                            elif i == 2: # is a header
                                scale *= 1.2
                        else:
                            scale *= 1
                    except KeyError:
                        scale *= 1
                tf = 1 + np.log10(appearances) # tf
                idf = np.log10(N/len(postings)) # idf
                score = tf*idf*scale
                try:
                    tf_idf[word].update({docID: score})
                except KeyError:
                    tf_idf[word] = ({docID: score})
                try:
                    simhash_dict[docID].update({sim_hashfn(word): score})
                except KeyError:
                    simhash_dict[docID] = {sim_hashfn(word): score}

            json.dump({word:f2.tell()}, f3)
            f3.write('\n')
            json.dump(tf_idf, f2)
            f2.write('\n')
    f1.close()
    f2.close()
    f3.close()

    # calculate simhash
    f = open("simhash_scores.json", 'w')
    for ID, hashed_words in simhash_dict.items():
        simhash_score = ''
        for i in range(64): # all hashed words are 64 bit binary strings
            i_th_binary = 0 # the i-th binary value
            for hashed_word, weight in hashed_words.items():
                if hashed_word[i] == '0':
                    i_th_binary -= weight
                elif hashed_word[i] == '1':
                    i_th_binary += weight
            if i_th_binary > 0:
                simhash_score += '1'
            else:
                simhash_score += '0'
        json.dump({ID:simhash_score}, f)
        f.write("\n")
    f.close()



def query_prompt():
    ps = PorterStemmer()
    tokenizer = RegexpTokenizer(r"[a-zA-Z0-9']+")

    # start prompt
    start = input("Enter 'start'(s) to get started or 'quit'(q) to quit: \n")
    start = start.lower()
    while(start != "start" and start != "s"):
        if start == 'q' or start == 'quit':
            exit()
        start = input("Unknown command, try again: \n")

    # loading auxillary structs
    print("Getting ready...")
    stop_words = set(stopwords.words("english"))
    info = (pickle.load( open( "info.p", 'rb' ) ))
    urls = info[0] # ID --> url dict
    limit = 5 # limit of number of websites shown *-1* no limit
    fp_dict = {}
    simhash_scores = {}
    with open("fp.json") as f:
        for line in f:
            fp_dict.update(json.loads(line)) # dict of the file pointers
    with open("simhash_scores.json") as f:
        for line in f:
            simhash_scores.update(json.loads(line))
    print(f"{len(fp_dict)} words in index")
    f = open("tf_idf.json") # open our index
    print("Ready, starting engine...")

    # engine start
    while True:
        try:
            query = input(">>> ")
            if query.lower() == 'q' or query == 'quit':
                print("quitting myEngine")
                break
            # something i added to set the number of documents to be shown
            lim_set = re.match(r'set_limit (\d+)', query)
            if lim_set != None:
                limit = int(lim_set[1])
                print(f"Limit set to {limit}")
                continue

            # start query and timer
            start = time.time()
            results = {}

            weights = list()
            parsed_query = tokenizer.tokenize(query)
            if len(parsed_query) == 0:
                print("Oops, empty query. Try again.")
                continue

            # removes stopwords that are irrelevent
            num_stopwords = 0
            for w in parsed_query:
                if w in stop_words:
                    num_stopwords += 1
            if num_stopwords/len(parsed_query) > .75:
                pass
            else:
                for w in list(parsed_query):
                    if w in stop_words:
                        parsed_query.remove(w)

            #getting all the weights for the rankings
            for w in parsed_query:
                try:
                    fp = fp_dict[ps.stem(w).lower()]
                except:
                    continue
                f.seek(fp)
                jsonObj = json.loads(f.readline())
                print(jsonObj.keys())
                score = list(jsonObj.values())[0]
                weights.append(score)

            # ranking documents via relevence score
            weights = sorted(weights, key = lambda x: len(x))
            for docID, doc_score in weights[0].items():
                normalize_factor = doc_score**2
                total = doc_score
                for i in range(len(weights)-1):
                    try:
                        next_score = weights[i+1][docID]
                        normalize_factor += next_score**2
                        total += next_score
                    except KeyError:
                        continue
                results[docID] = total/np.sqrt(normalize_factor)
            ranked_results = [x for x, y in sorted(results.items(), key = lambda x: x[1], reverse = True)]
            
            # removing near duplicates
            skip_counter = 0
            iteration_counter = 0
            simhashed_results = []
            if limit >= len(ranked_results):
                simhashed_results = ranked_results
            else:
                for i in range(limit):
                    top_ranked = str(ranked_results[0])
                    simhashed_results.append(top_ranked)
                    curr_simhash = simhash_scores[top_ranked]
                    ranked_results.remove(top_ranked)
                    for docID in list(ranked_results):
                        if skip_counter == 20 or iteration_counter == 50:
                            break # for optimization
                        same_bit_count = 0
                        for j in range(64):
                            if simhash_scores[docID][j] == curr_simhash[j]:
                                same_bit_count += 1
                        similarity = same_bit_count/64
                        #print (similarity)
                        if similarity > .8:
                            ranked_results.remove(docID)
                            skip_counter += 1
                        iteration_counter += 1
        except IndexError:
            print(f"No websites that match query <{query}>")
            continue

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
        end = time.time()

        print(f"Websites for your query <{query}>:\n")
        counter = 1
        for i in simhashed_results:
            print(f'{counter}. ID={i}: {urls[int(i)]}\n')
            counter += 1
        print(f"Query search time for <{query}>: {(end - start)*1000} milliseconds")

def main():
    #makeIndex()
    #merge_partitions()
    #delete_partitions()
    #calculate_helpers()
    query_prompt()
    return 0
    
if __name__=='__main__':
    main()