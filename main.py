"""
Date    : 10/01/2023
Version : 0.0.0
Author  : Mohan Teja G
Purpose : to extract textual data articles from the given URL and perform text analysis to compute variables
"""

#imports 
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import re
import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
import itertools
from tqdm import tqdm


#getting the input URLs
urls = pd.read_excel("./Input.xlsx")["URL"]


personal_pronouns = [ 'I' ,'we', 'my' ,'ours','us']
stop_words = set(stopwords.words("english"))
with open("./MasterDictionary/positive-words.txt", "r") as file:
    pos_words = [word.replace("\n",'') for word in file.readlines()]
with open("./MasterDictionary/negative-words.txt", "r") as file:
    neg_words = [word.replace("\n",'') for word in file.readlines()]

# Start a new browser session
driver = webdriver.Chrome()


def getContent(url="https://insights.blackcoffer.com/ai-in-healthcare-to-improve-patient-outcomes/"):
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    try:
        element = wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/div[6]/article/div[2]/div/div[1]/div/div[1]")))
        innerHTML = element.get_attribute("innerHTML")
        content =  re.sub(r'<.*?>', '', innerHTML)
    except:
        content = ''
    return content

def countSyllable(string):
    vowlels = ['a','e','i','o','u']
    temp  = string
    if(string[-2:]=="es" or string[-2:]=="ed"):
        temp = string[:-2]
    count = 0
    for char in temp:
        if(char in vowlels):
            count+=1
    return count
    
df = {
'url':[],
'POSITIVE SCORE':[],
'NEGATIVE SCORE':[],
'POLARITY SCORE':[],
'SUBJECTIVITY SCORE':[],
'AVG SENTENCE LENGTH':[],
'PERCENTAGE OF COMPLEX WORDS':[],
'FOG INDEX':[],
'AVG NUMBER OF WORDS PER SENTENCE':[],
'COMPLEX WORD COUNT':[],
'WORD COUNT':[],
'SYLLABLE PER WORD':[],
'PERSONAL PRONOUNS':[],
'AVG WORD LENGTH':[]
}

for url in tqdm(urls,desc="loading.. "):
    content = getContent(url)
    if(content==''):
        print("page error : ", url)
    sentences = sent_tokenize(content)
    # removes all the punctuation marks
    sentences = [re.sub(r'[^\w\s]', '', sentence) for sentence in sentences]
    #word tokenized sentence
    sentences = [word_tokenize(sentence) for sentence in sentences]
    try:
        avg_words_sentence = sum([len(sentence) for sentence in sentences])/len(sentences)
    except ZeroDivisionError:
        avg_words_sentence = 0

    words = list(itertools.chain.from_iterable(sentences))

    n_personal_pronouns = sum([1 if word in personal_pronouns else 0 for word in words])


    cleaned = [word for word in words if word.lower() not in stop_words ]

    try:
        avg_word_len = len(''.join(cleaned))/len(cleaned)
    except ZeroDivisionError:
        avg_word_len = 0

    pos_score = 0
    neg_score = 0
    for word in cleaned:
        if(word.lower() in pos_words):
            pos_score+=1
        if(word.lower() in neg_words):
            neg_score-=1
    neg_score = neg_score*-1

    polarity_score = (pos_score-neg_score)/((pos_score+neg_score)+0.000001)
    subjectivity_score = (pos_score+neg_score)/(len(cleaned)+0.000001)

    try :
        avg_sentence_len = len(words)/len(sentences)
    except ZeroDivisionError:
        avg_sentence_len = 0



    sy_counts = [countSyllable(word) for word in cleaned]
    try:
        avg_sy_word = sum(sy_counts)/len(sy_counts)
    except ZeroDivisionError:
        avg_sy_word = 0
    
    nComplex  = sum([1 if count>2 else 0 for count in sy_counts])
    try:
        pComplex  = nComplex/len(cleaned)
    except ZeroDivisionError:
        pComplex = 0

    fog_index = 0.4*(avg_sentence_len+pComplex)

    df['url'].append(url),
    df['POSITIVE SCORE'].append(pos_score)
    df['NEGATIVE SCORE'].append(neg_score)
    df['POLARITY SCORE'].append(polarity_score)
    df['SUBJECTIVITY SCORE'].append(subjectivity_score)
    df['AVG SENTENCE LENGTH'].append(avg_sentence_len)
    df['PERCENTAGE OF COMPLEX WORDS'].append(pComplex)
    df['FOG INDEX'].append(fog_index)
    df['AVG NUMBER OF WORDS PER SENTENCE'].append(avg_words_sentence)
    df['COMPLEX WORD COUNT'].append(nComplex)
    df['WORD COUNT'].append(len(cleaned))
    df['SYLLABLE PER WORD'].append(avg_sy_word)
    df['PERSONAL PRONOUNS'].append(n_personal_pronouns)
    df['AVG WORD LENGTH'].append(avg_word_len)

df = pd.DataFrame.from_dict(df)

df.to_excel("output.xlsx")  

driver.quit()