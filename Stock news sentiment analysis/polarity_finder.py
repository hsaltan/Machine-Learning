# Import libraries
import sys
sys.path.insert(1, '/scripts')
import AWSResourceDeploy as aws
from bs4 import BeautifulSoup 
import requests
import psycopg2
from colorama import Fore, Back, Style
from textblob import TextBlob
import re
from sklearn.feature_extraction.text import CountVectorizer
from nltk.tag import pos_tag
from nltk.stem.wordnet import WordNetLemmatizer


# Define the region and boto3 clients
region = "eu-west-1"

# Database credentials
dbiParamName = "dbInstanceIdentifier"
userPasswordParamName = "masterUserPassword"
dbInstanceIdentifier = aws.get_parameter(dbiParamName, region)
masterUserPassword = aws.get_parameter(userPasswordParamName, region)
endpoint, port, usr, dbName = aws.describe_rds(dbInstanceIdentifier, region)

# Open the database connection
conn = psycopg2.connect(host=endpoint, port=port, database=dbName, user=usr, password=masterUserPassword)
cur = conn.cursor()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

# Find the link, article id and the related ticker to scrape the relevant content
def find_row_data():
    global articleID, ticker, link
    q = "SELECT ARTICLE_ID, SYMBOL, LINK FROM articles WHERE LINK IS NOT NULL AND {a} IS NULL AND {b} IS NULL ORDER BY ARTICLE_ID ASC LIMIT 1".format(a=column1, b=column2)
    cur.execute(q)
    row = cur.fetchone()
    articleID = row[0]
    ticker = row[1]
    link = row[2]
    return articleID, ticker, link

# Find the the words of query to search for relevant content in the article
def get_query_words():
    cur.execute("SELECT NAME FROM stocks WHERE SYMBOL = '{}'".format(ticker))
    query_words = cur.fetchone()[0].split()
    if query_words[1][-1] == ".":
        query_words[1] = query_words[1][:-1]

    # Query is the ticker of the company and the first two words of the name of the company
    oneWord = query_words[0].lower()
    twoWord = " ".join(query_words[0:2]).lower()
    if len(ticker) > 2:
        acceptableTicker = ticker.lower()
    else:
        acceptableTicker = oneWord
    return acceptableTicker, oneWord, twoWord

# Scrape the link
def scrape_page():
    find_row_data()
    r = requests.get(link, headers=headers)
    c = r.content
    soup = BeautifulSoup(c, "html.parser")
    paragraphs = soup.find_all('p')
    return paragraphs

# Extract the relevant text for further analysis
def extract_corpus():
    articleText = ""
    paragraphs = scrape_page()
    for paragraph in paragraphs:
        paragraphText = paragraph.text.replace("\xa0", "").replace("\n", "")
        paragraphText = re.sub("https?:\/\/(www\.)?\S+","", paragraphText)
        paragraphText = re.sub("[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+","", paragraphText)    
        paragraphText = re.sub("[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+","", paragraphText)
        articleText = articleText + " " + paragraphText

    # Split the text by "." and space
    sentences = re.split('[.]\s', articleText)

    # Convert to lowercase
    lower_sentences = [x.lower() for x in sentences]

    # Put the sentences in order in a dictionary
    numbered_sentences = {}
    sequences = range(len(lower_sentences))  
    for sequence in sequences:
        numbered_sentences[sequence+1] = lower_sentences[sequence]
    arranged_sentences = []

    # Find the sentence where one of the query statements are located and the following sentence, and add them to a list
    acceptableTicker, oneWord, twoWord = get_query_words()
    for key, value in numbered_sentences.items():
        if acceptableTicker in value or oneWord in value or twoWord in value:
            arranged_sentences.append(numbered_sentences[key])
            try:
                arranged_sentences.append(numbered_sentences[key+1])
            except:
                pass
    
    # Transfer the relevant sentences in order to a list
    corpus = list(dict.fromkeys(arranged_sentences))
    corpus = [x.replace(acceptableTicker, "").replace(oneWord, "").replace(twoWord, "") for x in corpus]
    return corpus

# Clean the relevant text and prepare it for the sentiment analysis
def clean_article():

    # Get the relevant text
    corpus = extract_corpus()

    # Tokenize the text
    vectorizer = CountVectorizer(stop_words='english')
    try:
        vectorizer.fit_transform(corpus)
        feature_names = vectorizer.get_feature_names()
    except Exception:
        feature_names = str(0)

    # Find part of speech
    tagged_names = pos_tag(feature_names)

    # Filter out numbers and nonsensical words
    filtered_tagged_names = list(filter((lambda x: x[1] != 'CD'), tagged_names))

    # Lemmatize the names
    lemmatized_words = []
    lemmatizer = WordNetLemmatizer()

    for name, pos in filtered_tagged_names:
        if pos.startswith("NN"):
            lemmatized_words.append(lemmatizer.lemmatize(name, pos="n"))
        elif pos.startswith('VB'):
            lemmatized_words.append(lemmatizer.lemmatize(name, pos="v"))
        elif pos.startswith('JJ'):
            lemmatized_words.append(lemmatizer.lemmatize(name, pos="a"))
        else:
            lemmatized_words.append(name)

    # Convert the lemmatized words into a text
    final_text = ""

    for lemmatized_word in lemmatized_words:
        final_text = final_text + lemmatized_word + " "

    return final_text

# Find the polarity score of the relevant content of the article
def find_polarity_score():
    if final_text:
        # Find the TextBlob polarity score
        polarityScore = round(TextBlob(final_text).polarity, 5)
    else:

        # If there exists no text to study, set the polarity score to 2 to later eliminate it in the analysis
        polarityScore = 2.0
    return polarityScore

# Write the polarity score in the database
def write_polarity_scores():
    polarityScore = find_polarity_score()
    cur.execute("UPDATE articles SET POLARITY = {a} WHERE ARTICLE_ID = '{b}'".format(a=polarityScore, b=articleID))
    conn.commit()
    return polarityScore

# Find the AWS Comprehend sentiment score
def find_aws_polarity_score(final_text):
    numberOfBytesString = len(final_text.encode('utf-8'))
    if numberOfBytesString <= 5000:
        positive, negative, neutral, mixed = aws.detect_sentiment(final_text, region, language='en')
        awsPolarityScore = positive - negative
    else:
        awsPolarityScore = 2.0
    return awsPolarityScore

# Write the AWS Comprehend sentiment score in the database
def write_aws_sentiment_scores():
    if n <= awsRecords and final_text:
        awsPolarityScore = round(find_aws_polarity_score(final_text), 7)

    # If there exists no text to study or the limit for links to find the sentiment score is reached, set the sentiment score to 2
    else:
        awsPolarityScore = 2.0
    cur.execute("UPDATE articles SET AWS_POLARITY = {a} WHERE ARTICLE_ID = '{b}'".format(a=awsPolarityScore, b=articleID))
    conn.commit()
    return awsPolarityScore

# Find the total number of records in the table and the number of article links to be studied
def count_records():
    cur.execute("SELECT count(*) FROM articles WHERE LINK IS NOT NULL AND POLARITY IS NULL")
    totalNumberOfRecords = cur.fetchall()[0][0]
    print('\n')
    if totalNumberOfRecords > 0:
        records = int(input(f"{Fore.MAGENTA}Enter the number of article links that you want to find the {Fore.RED}polarity score{Style.RESET_ALL}{Fore.MAGENTA}, between 0 and {totalNumberOfRecords}; 0 for none:{Style.RESET_ALL} {Fore.YELLOW}"))
    else:
        records = 0
    print('\n')
    cur.execute("SELECT count(*) FROM articles WHERE LINK IS NOT NULL AND AWS_POLARITY IS NULL")
    nullAwsPolarityRecords = cur.fetchall()[0][0]
    if nullAwsPolarityRecords > 0:
        awsRecords = int(input(f"{Fore.MAGENTA}Enter the number of article links that you want to find the {Fore.RED}AWS Comprehend sentiment score{Style.RESET_ALL}{Fore.MAGENTA}, between 0 and {nullAwsPolarityRecords}; 0 for none:{Style.RESET_ALL} {Fore.YELLOW}"))
    else:
        awsRecords = 0
    print('\n')
    return records, awsRecords

# Find the number of records to calculate the sentiment scores
records, awsRecords = count_records()

# Get the polarity scores and enter them in the database table
print(f"{Fore.MAGENTA}Polarity and/or sentiment scores for the{Style.RESET_ALL} {Fore.CYAN}{records}{Style.RESET_ALL} {Fore.MAGENTA}links are (polarity score of 2.0 means 'None'): {Style.RESET_ALL}")
print('\n')

# It's up to the researcher to find TextBlob and/or AWS Comprehend sentiment score for any number of links
# There can be different number of links for each score calculation
n = 1

if records == 0:
    print(f"{Fore.RED}There is not any link to calculate polarity score{Style.RESET_ALL}")
    print('\n')
    # Calculate AWS score only
    if awsRecords >= 0:
        for r in range(awsRecords):
            column1 = "AWS_POLARITY"
            column2 = "AWS_POLARITY"
            final_text = clean_article()
            awsPolarityScore = write_aws_sentiment_scores()
            n += 1
            print(f"{Fore.RED}{r+1}.{Style.RESET_ALL}\t{Fore.CYAN}{link}{Style.RESET_ALL}\t{Fore.MAGENTA}AWS:{Style.RESET_ALL} {Fore.GREEN}{awsPolarityScore}{Style.RESET_ALL}")
    # No calculation of any score
    else:
        print(f"{Fore.MAGENTA}There is not any link to calculate neither{Style.RESET_ALL} {Fore.RED}polarity{Style.RESET_ALL} {Fore.MAGENTA}nor{Style.RESET_ALL} {Fore.RED}AWS Comprehend sentiment score{Style.RESET_ALL}")
        print('\n')
        sys.exit()
elif records > 0:
    # Calculate only TextBlob score
    if awsRecords == 0:
        for r in range(records):
            print(f"{Fore.MAGENTA}There is not any link to calculate{Style.RESET_ALL} {Fore.RED}AWS Comprehend sentiment score{Style.RESET_ALL}")
            print('\n')
            column1 = "POLARITY"
            column2 = "POLARITY"
            final_text = clean_article()
            polarityScore = write_polarity_scores()
            print(f"{Fore.RED}{r+1}.{Style.RESET_ALL}\t{Fore.CYAN}{link}{Style.RESET_ALL}\t{Fore.MAGENTA}TBL:{Style.RESET_ALL} {Fore.GREEN}{polarityScore}{Style.RESET_ALL}")
    # Calculate both scores
    else:
        # Calculate both for the same number of links
        minLoops = min(records, awsRecords)
        for r in range(minLoops):
            column1 = "POLARITY"
            column2 = "AWS_POLARITY"
            final_text = clean_article()
            polarityScore = write_polarity_scores()
            awsPolarityScore = write_aws_sentiment_scores()
            n += 1
            print(f"{Fore.RED}{r+1}.{Style.RESET_ALL}\t{Fore.CYAN}{link}{Style.RESET_ALL}\t{Fore.MAGENTA}TBL:{Style.RESET_ALL} {Fore.GREEN}{polarityScore}{Style.RESET_ALL}\t{Fore.MAGENTA}AWS:{Style.RESET_ALL} {Fore.GREEN}{awsPolarityScore}{Style.RESET_ALL}")
        # Calculate either score for the extra links
        maxLoops = max(records, awsRecords)
        # TextBlob
        if records > awsRecords:
            for r in range(minLoops, maxLoops):
                column1 = "POLARITY"
                column2 = "POLARITY"
                final_text = clean_article()
                polarityScore = write_polarity_scores()
                print(f"{Fore.RED}{r+1}.{Style.RESET_ALL}\t{Fore.CYAN}{link}{Style.RESET_ALL}\t{Fore.MAGENTA}TBL:{Style.RESET_ALL} {Fore.GREEN}{polarityScore}{Style.RESET_ALL}")
        elif records < awsRecords:
            # AWS
            for r in range(minLoops, maxLoops):
                column1 = "AWS_POLARITY"
                column2 = "AWS_POLARITY"
                final_text = clean_article()
                awsPolarityScore = write_aws_sentiment_scores()
                n += 1
                print(f"{Fore.RED}{r+1}.{Style.RESET_ALL}\t{Fore.CYAN}{link}{Style.RESET_ALL}\t{Fore.MAGENTA}AWS:{Style.RESET_ALL} {Fore.GREEN}{awsPolarityScore}{Style.RESET_ALL}")
conn.close()
print('\n')
