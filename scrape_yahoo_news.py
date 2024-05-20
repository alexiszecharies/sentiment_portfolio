import openai
openai.api_key = ""
import feedparser
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import csv
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'
}

chat_gpt_sentiment_question = "Tell me if it's a good or bad piece of news"
chat_gpt_summary_question = "Give me a summary of this financial news no longer than 60 words"
chat_gpt_NYSE_question = "Which NYSE or NASDAQ companies are in this in this article? If any, what is their ticker?"
translation_question = "Take the following text in ''' ''' and translate to spanish "
rss_link = 'https://finance.yahoo.com/rss/'

output_file_path = 'yahoo_finance_chat_GPT.csv'
columns = ['article_url', 'title', 'timestamp', 'published_date', 'news_text',
           'summary_gpt' , 'sentiment_gpt', 'sentiment', 'ticker_gpt', 'tickers', 'translation_GPT']
useful_columns = ['published_date', 'article_url','summary_gpt', 'sentiment', 'tickers', 'translation_GPT']
output_file_path_trimmed = 'yahoo_finance_chat_GPT_trimmed.csv'

def get_yahoo_news_text_and_tickers(url):
  response = requests.get(url, timeout = 10, headers = headers)
  if response.status_code == 200:
    text = ''
    ticker_texts = '-'
    # Parse the content using BeautifulSoup with 'html.parser' as the parser
    soup = BeautifulSoup(response.content, 'html.parser')

    # Get the element with class 'caas-body'
    caas_body = soup.find(attrs={'class': 'caas-body'})

    # Find elements with class 'xray-card-click-target caas-button'
    ticker_elements = soup.find_all(attrs={'class': 'xray-card-click-target caas-button'})

    # If the element is found
    if caas_body:
        # Find all the elements with the class 'caas-list caas-list-bullet' within the 'caas-body' and decompose (remove) them
        for element in caas_body.find_all(class_='caas-list caas-list-bullet'):
            element.decompose()

        # Extract the text from the 'caas-body'
        text = caas_body.get_text()

        try:
            ticker_elements = [element['aria-label'] for element in ticker_elements]
            ticker_texts = ','.join(ticker_elements)
            if ticker_texts == '':
                    ticker_texts = '-'
        except:
            ticker_texts = '-'
    return(text, ticker_texts)
  else:
    #print('trying zenrows')
    #client = ZenRowsClient("74495e1b572c979e77d80fc0ce3df2fe462a0cb0")
    #response = client.get(url)
    #if response.status_code == 200:
    #  soup = BeautifulSoup(response.text, 'html.parser')
    #  return soup.find('div', attrs={'class': 'caas-body'}).text
    #else:
    print('error getting yahoo news ', url)
    return('error', 'error')

def chat_with_GPT(prompt):
  completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo-16k",
    messages=[
      {"role": "user", "content": prompt}
    ]
  )
  response = completion.choices[0].message.content
  return response

def check_if_output_file_path_exists_if_not_create_with_columns(output_file_path, columns_home_page_scrape):
  try:
    csvfile = open(output_file_path, "r")
    csvfile.close()
  except:
    with open(output_file_path, "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns_home_page_scrape)
        writer.writeheader()

def extract_sentiment(text): #text must be on lowercases
  if 'good news' in str(text) or 'good piece of news' in str(text):
    return 'good'
  elif 'bad news' in str(text) or 'bad piece of news' in str(text):
    return 'bad'
  elif 'neutral' in str(text):
    return 'neutral'
  elif 'mixed' in str(text):
    return 'mixed'
  else:
    return 'neutral'
"""
def extract_tickers(gpt_text, news_text, tickers_df):
  tickers = list(tickers_df['ticker'].astype(str))
  tickers_found = []
  for ticker in tickers:
    if ' ' + ticker + ' ' in gpt_text or '(' + ticker + ')' in gpt_text or ' ' + ticker + ')' in gpt_text or ' ' + ticker + '.' in gpt_text or ' ' + ticker + '\n' in gpt_text:
      tickers_found.append(ticker)
  # lo que viene aca abajo son fixes a problemas con tickers de una letra que son medio bravos
  class_letters = ['A', 'B', 'C', 'D', 'E']
  for letter in class_letters:
    if letter in tickers_found and 'Class ' + letter in gpt_text:
      tickers_found = [x for x in tickers_found if x != letter]
  if 'U' in tickers_found and 'U.S.' in gpt_text:
    tickers_found = [x for x in tickers_found if x != 'U']
  regex_find_list = re.findall(r'\((.*?)\)', gpt_text.replace('NYSE: ', '').replace('NASDAQ: ', '').replace('^', '').replace('NYSE:', '').replace('NASDAQ:', '')) # como algunos tickers no estan en mi archivo busco todo lo que este entre ()
  regex_find_list = [x for x in regex_find_list if x.isupper()]

  #extraction 2
  comp_dict = dict(zip(tickers_df['name'], tickers_df['ticker']))
  names = list(tickers_df['name'].astype(str))
  for name in names:
    if name in news_text[:-400]:
      tickers_found.append(comp_dict[name])
  tickers_found = [x for x in tickers_found if x not in ['NDAQ', 'DOW', 'TWOA', 'RDY', 'DNOW', 'DAVE']]

  #dedup
  tickers_found = list(set(regex_find_list + tickers_found))
  tickers_found = [x.split('.')[0] for x in tickers_found] # arregla un caso medio excepcional PACW.O que venia con un punto algun motivo
  return ','.join(tickers_found) if tickers_found != [] else '-'
"""

def translate_summary(eng_text):
  try:
    return chat_with_GPT(translation_question + eng_text)
  except:
    return ''

max_retries = 10
retry_interval = 1 # cuanto esperar antes de volver a mandar request a chatgpt despues de encontrar un error (creo que cuando le mandamos cosas muy largas no solo esta el limite de requests per minute pero token tambien)
requests_per_second_limit = 0 #60/3 + 1 # 3 requests por minuto # ahora que pagamos no esta esta restriccion
"""
tickers_df = pd.read_csv('us_symbols.csv')
strings_to_replace = [' Inc.', ' inc.',' Ltd.', ' INC.', ' LTD.', ' LTD', ' Inc', ' Ltd', ' Corporation', ' Corp.', ' Corp', ' PLC', ' plc', ' S.A.', ' Limited', ' Sponsored']

tickers_df['name'] = tickers_df['name'].replace(strings_to_replace, '', regex=True)
tickers_df['name'] = tickers_df['name'].apply(lambda x: x.split('(')[0])
tickers_df['name'] = tickers_df['name'].str.strip()
tickers_df['name'] = tickers_df['name'].str.replace('Corporation', '')
"""

check_if_output_file_path_exists_if_not_create_with_columns(output_file_path, columns)
df = pd.read_csv(output_file_path)
already_processed_articles = list(df['article_url'])

# Collect RSS feed
print('parsing feed')
feed = feedparser.parse(rss_link)
print('done parsing feed')

list_news = []

# Iterate over feed entries
for entry in feed.entries:
  news_dict = {}
  article_url = entry.link
  if 'finance.yahoo.com/news/' in article_url:
    title = entry.title
    news_dict['article_url'] = article_url
    news_dict['title'] = title
    news_dict['timestamp'] = entry.published
    news_dict['published_date'] = entry.published[:10]
    list_news.append(news_dict)

for art_dict in list_news:
  if art_dict['article_url'] not in already_processed_articles:
    print('New article to scrape: ', art_dict['article_url'])
    news_text, tickers = get_yahoo_news_text_and_tickers(art_dict['article_url'])
    print('tickers ',  tickers)
    art_dict['news_text'] = news_text
    if art_dict['news_text'] != 'error':
      for i in range(max_retries):
        try:
          art_dict['sentiment_gpt'] = chat_with_GPT(chat_gpt_sentiment_question + art_dict['news_text'])
          art_dict['sentiment'] = extract_sentiment(art_dict['sentiment_gpt'].lower())
          time.sleep(requests_per_second_limit)# requests to chatgpt per minute with our plan
          art_dict['summary_gpt'] = chat_with_GPT(chat_gpt_summary_question + art_dict['news_text'])
          time.sleep(requests_per_second_limit)
          art_dict['ticker_gpt'] = "-"
          art_dict['tickers'] = tickers
          art_dict['translation_GPT'] = translate_summary(art_dict['summary_gpt'])
          time.sleep(requests_per_second_limit)
          with open(output_file_path, "a") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writerow(art_dict)
        except Exception as e:
          print(str(e))
          if "This model's maximum context length is" in str(e):
            print(f"Exception occurred: {str(e)}")
            #no se puede mandar el articulo a chat GPT porque es muy largo
            art_dict['sentiment_gpt'] = art_dict['sentiment'] = art_dict['summary_gpt'] = art_dict['ticker_gpt'] = "articulo muy largo para chatGPT"
            with open(output_file_path, "a") as csvfile:
              writer = csv.DictWriter(csvfile, fieldnames=columns)
              writer.writerow(art_dict)
            break
          else:
            #si no es ese error, espera un poco y volve a intentar
            print(f"Exception occurred: {str(e)}. Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)
        else:
          # en caso de que no haya un exception, anduvo todo, sali de este loop for y anda al proximo articulo
          break
      else:
        # If all retries have failed, raise an exception or return an error message
        raise Exception("Failed after multiple retries.")
    else:
      print('error with article ', art_dict['article_url'])

print("Successful run")

df = pd.read_csv(output_file_path)
df = df.sort_values(by = ['published_date'], ascending=False)
df.to_csv(output_file_path, index = False, encoding = 'utf-8')
df[useful_columns].to_csv(output_file_path_trimmed, index = False, encoding = 'utf-8')

#df[['article_url', 'published_date', 'summary_gpt', 'tickers']].to_excel(output_file_path.replace('csv', 'xls'), index = False)
print(df.head())