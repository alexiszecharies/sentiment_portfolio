import streamlit as st
import pandas as pd
from datetime import datetime, time
import html
import unicodedata

def remove_accents(texto):
    texto_normalizado = unicodedata.normalize('NFD', texto)
    texto_sin_acentos = ''.join(c for c in texto_normalizado if not unicodedata.combining(c))
    return texto_sin_acentos

selected_language = "English" #default
path = ''
csv_path = path + 'yahoo_finance_chat_GPT_trimmed.csv'
logo_path = path + 'Logo.png'
clouds_path = path + 'clouds.png'
background_color = '#070E27'
table_header_text = '<table><tr><th>Published Date</th><th>Article URL</th><th>Summary chatGPT</th><th>Sentiment</th><th>News Tickers</th></tr>'
table_header_text_esp = '<table><tr><th>Fecha de publicación</th><th>URL del artículo</th><th>Resumen chatGPT</th><th>Sentimiento</th><th>Tickers de la noticia</th></tr>'
filter_terms_text = "Filter terms in news summary. Example: inflation, rates, unemployment, GDP, FED"
filter_terms_text_esp = "Filtra términos en el resumen de noticias. Ejemplo: inflación, tasas, desempleo, PIB, FED"
filter_tickers_text = "Filter tickers separated by commas and click enter. Example: TSLA,META"
filter_tickers_text_esp = "Filtra símbolos separados por comas y haz clic en enter. Ejemplo: TSLA, META"
start_date_text = "Start date"
start_date_text_esp = "Fecha de inicio"
end_date_text = "End date"
end_date_text_esp = "Fecha de finalización"
select_number_of_results = "Number of results to display"
select_number_of_results_esp = "Número de resultados a mostrar"
sentiment_text = "Sentiment"
sentiment_text_esp = "Sentimento"
useful_columns = ['published_date', 'article_url','summary_gpt', 'sentiment', 'news_tickers', 'sentiment_esp', "translation_GPT"]
# Define CSS styles
css = f"""
    <style>
    body {{
        background-color: {background_color};
    }}
    </style>
"""
st.set_page_config(layout="wide", page_icon=clouds_path, page_title = 'Skyblue Analytics')

# Create a selectbox widget for language selection
available_languages = {
    "English": "en",
    "Español": "es",
    # Add more languages as needed
}

#selected_language = st.sidebar.selectbox("Select language", list(available_languages.keys()))

# Display the CSS styles
st.markdown(css, unsafe_allow_html=True)

#st.image(logo_path)#/Users/alexiszecharies/Documents/GitHub/medspy/yahoo/Logo.png

df = pd.read_csv(csv_path, encoding='utf-8')
df = df.dropna()
df = df.drop_duplicates(subset = ['article_url'])
df = df[df['summary_gpt'] != 'articulo muy largo para chatGPT']

df['news_tickers'] = df['tickers'].str.replace(',', '\n')

df['tickers'] = ',' + df['tickers'].str.split('.').str[0] + ',' #having a ticker separator as ,ticker, for all cases
df['sentiment'] = df['sentiment'].map({'good':'Good','bad':'Bad','neutral':'Neutral', 'mixed':'Mixed'})
df['sentiment_esp'] = df['sentiment'].map({'Good':'Bueno','Bad':'Malo','Neutral':'Neutral', 'Mixed':'Mixto'})

# Function to convert DataFrame to HTML with clickable links
def make_clickable(val):
    return '<a href="{}">Link</a>'.format(val,val)

# Create a date range input widget
col3, col4, col5, col6, col7 = st.columns(5)
with col7:
    selected_language = st.selectbox(' ', list(available_languages.keys()))
b_english = available_languages[selected_language] == 'en'
with col3:
    start_date = st.date_input(start_date_text if b_english else start_date_text_esp, value=datetime(2023, 5, 8))
with col4:
    end_date = st.date_input(end_date_text if b_english else end_date_text_esp)
with col5:
    # Create a number input widget
    num_results = st.number_input(select_number_of_results if b_english else select_number_of_results_esp, min_value=1, max_value=len(df), value=100)
with col6:
# List of options for the checkboxes
    default_sentiment = "all" if b_english else "todos"
    if b_english:
        options_sentiment = df['sentiment'].value_counts().index.tolist()
    else:
        options_sentiment = df['sentiment_esp'].value_counts().index.tolist()

    options_sentiment.append(default_sentiment)
    # Create a selectbox with default value
    selected_sentiment = st.selectbox(sentiment_text if b_english else sentiment_text_esp, options_sentiment, index=options_sentiment.index(default_sentiment))

# Create a text input widget
col1, col2 = st.columns(2)
with col1:
    user_input_ticker_list = st.text_input(filter_tickers_text if b_english else filter_tickers_text_esp).replace(' ', '').upper().split(',')
with col2:
    user_input_term_list = st.text_input(filter_terms_text if b_english else filter_terms_text_esp).lower().split(',')

# Create a checkbox
#checked = st.checkbox("Check me!")

# Set the language for the app
st.session_state.language = available_languages[selected_language]

# Filter DataFrame based on user input
if user_input_ticker_list == ['']:
    ticker_filter =  df['tickers'] ==  df['tickers'] #all true show all
else:
    user_input_tickers = [ ',' + x + ',' for x in user_input_ticker_list]
    ticker_filter = df['tickers'].str.contains('|'.join(user_input_tickers))

if user_input_term_list == ['']:
    user_term_filter =  df['tickers'] ==  df['tickers'] #all true show all
else:
    if b_english:
        user_term_filter = df['summary_gpt'].str.lower().apply(lambda x: all(' ' + word + ' ' in x for word in user_input_term_list))
    else:
        user_term_filter = (df['summary_gpt'].str.lower().apply(lambda x: all(' ' + remove_accents(word) + ' ' in remove_accents(x) for word in user_input_term_list))) \
                            | (df['translation_GPT'].str.lower().apply(lambda x: all(' ' + remove_accents(word) + ' ' in remove_accents(x) for word in user_input_term_list)))

# Apply date range filter
if start_date is not None and end_date is not None:
    df['published_date_modified'] = pd.to_datetime(df['published_date'])  # Convert to datetime type
    date_filter = (df['published_date_modified'] >= datetime.combine(start_date, time.min)) & (df['published_date_modified'] <= datetime.combine(end_date, time.max))
else:
    date_filter = df['tickers'] == df['tickers']  # all true show all

#sentiment filter
if selected_sentiment != default_sentiment:
    if b_english:
        sentiment_filter = df['sentiment'] == selected_sentiment
    else:
        sentiment_filter = df['sentiment_esp'] == selected_sentiment
else:
    sentiment_filter = df['tickers'] == df['tickers']  #all true show all



# Get unique names for selectbox options
#sentiments = df['sentiment'].unique()

# Create a selectbox widget
#selected_name = st.selectbox('Select a sentiment', sentiments)

# Filter DataFrame based on selected name
#sentiment_filter = [df['sentiment'] == selected_name]

df_show = df[useful_columns][ticker_filter & user_term_filter & date_filter & sentiment_filter].head(num_results)

# Convert DataFrame to HTML
#df_styled = df_show.style.format({'article_url': make_clickable})
# Display HTML in Streamlit
#st.write(df_styled.render(), unsafe_allow_html=True)

# Create and display HTML table
#this is better since it removes the row number which comes bby default in df.render()

summary_column = "summary_gpt" if b_english else "translation_GPT"
sentiment_column = "sentiment" if b_english else "sentiment_esp"

html_data = table_header_text if b_english else table_header_text_esp
for i in range(len(df_show)):
    row = df_show.iloc[i]
    html_data += '<tr>'
    html_data += f'<td>{html.escape(str(row["published_date"]))}</td>'
    html_data += f'<td>{make_clickable(html.escape(str(row["article_url"])))}</td>'
    html_data += f'<td>{html.escape(str(row[summary_column])).replace("$", "&#36;")}</td>'  # Escape dollar sign
    html_data += f'<td>{html.escape(str(row[sentiment_column]))}</td>'
    html_data += f'<td>{html.escape(str(row["news_tickers"]))}</td>'
    html_data += '</tr>'
html_data += '</table>'


html_data = html_data.replace("&#x27;", "'")

# Display HTML in Streamlit
st.write(html_data, unsafe_allow_html=True)
