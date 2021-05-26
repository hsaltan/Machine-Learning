# Import libraries
import sys
sys.path.insert(1, '/scripts')
from colorama import Fore, Back, Style
from datetime import datetime, timedelta
from pandas_datareader import data
import AWSResourceDeploy as aws
import psycopg2


# Define the region and boto3 clients
region = "eu-west-1"

# Set the time periods
dates = ["P_at_0d", "P_bef_15d", "P_bef_7d", "P_bef_3d", "P_aft_3d", "P_aft_7d", "P_aft_15d"]
delta_days = [0, -15, -7, -3, 3, 7, 15]
numberOfDates = len(dates)

# Database credentials
dbiParamName = "dbInstanceIdentifier"
userPasswordParamName = "masterUserPassword"
dbInstanceIdentifier = aws.get_parameter(dbiParamName, region)
masterUserPassword = aws.get_parameter(userPasswordParamName, region)
endpoint, port, usr, dbName = aws.describe_rds(dbInstanceIdentifier, region)

# Open the database connection
conn = psycopg2.connect(host=endpoint, port=port, database=dbName, user=usr, password=masterUserPassword)
cur = conn.cursor()

# Write the stock price in the database table
def write_price(articleDate, ticker, date, stockPrice):
    cur.execute("UPDATE articles SET {a} = {b} WHERE SYMBOL = '{c}' AND ARTICLE_DATE = '{d}'".format(a=date, b=stockPrice, c=ticker, d=articleDate))
    conn.commit()

# Find the price at a particular date
def find_price(ticker, priceDate):
    panel_data = None 
    threshold = 1
    stockPrice = 0
    while panel_data is None and threshold <= 7:
        try:
            panel_data = data.DataReader(ticker, 'yahoo', priceDate, priceDate)
            stockPrice = round(panel_data.iat[-1, panel_data.columns.get_loc('Adj Close')], 4)
        # If no price at that date, go back by one day until finding one
        except:
            priceDate = priceDate - timedelta(days=1)
            threshold += 1
    return stockPrice

# Get article date
def find_date():
    table_record = {}
    cur.execute("SELECT ARTICLE_ID, SYMBOL, ARTICLE_DATE FROM articles WHERE POLARITY IS NOT NULL AND POLARITY <> 2.0 AND (P_at_0d IS NULL OR P_bef_15d IS NULL OR P_bef_7d IS NULL OR P_bef_3d IS NULL OR P_aft_3d IS NULL OR P_aft_7d IS NULL OR P_aft_15d IS NULL) ORDER BY ARTICLE_ID ASC LIMIT 1")
    row = cur.fetchone()
    articleID = row[0]
    ticker = row[1]
    articleDate = row[2]
    table_record['ticker'] = ticker
    table_record['article date'] = articleDate
    for item in range(numberOfDates):
        priceDate = articleDate + timedelta(delta_days[item])
        stockPrice = find_price(ticker, priceDate)
        date = dates[item]
        table_record[date] = stockPrice
        write_price(articleDate, ticker, date, stockPrice)
    print('\n')
    return table_record

# Find the total number of records in the table and the number of article links to be studied
def count_records():
    cur.execute("SELECT count(*) FROM articles WHERE POLARITY IS NOT NULL AND POLARITY <> 2.0 AND (P_at_0d IS NULL OR P_bef_15d IS NULL OR P_bef_7d IS NULL OR P_bef_3d IS NULL OR P_aft_3d IS NULL OR P_aft_7d IS NULL OR P_aft_15d IS NULL) GROUP BY SYMBOL, ARTICLE_DATE")
    query = cur.fetchall()
    totalNumberOfRecords = len(query)
    print('\n')
    records = int(input(f"{Fore.MAGENTA}Enter the number of article links that you want to find the stock prices, between 1 and {totalNumberOfRecords}:{Style.RESET_ALL} {Fore.YELLOW}"))
    print('\n')
    return records

# Get the number of article links that you want to find the stock prices
records = count_records()
print(f"{Fore.MAGENTA}Stock prices at the dates of{Style.RESET_ALL} {Fore.CYAN}{records}{Style.RESET_ALL} {Fore.MAGENTA}links are: {Style.RESET_ALL}")
print('\n')
for record in range(records):
    table_record = find_date()
    print(f"{Fore.RED}{record+1}.\t{Style.RESET_ALL}{Fore.LIGHTYELLOW_EX}{table_record['ticker']}\t{Style.RESET_ALL}{Fore.CYAN}{table_record['article date']}\t{Style.RESET_ALL}{Fore.MAGENTA}On the article date: {Style.RESET_ALL}{Fore.GREEN}{table_record['P_at_0d']}   {Style.RESET_ALL}{Fore.MAGENTA}15 days before: {Style.RESET_ALL}{Fore.GREEN}{table_record['P_bef_15d']}   {Style.RESET_ALL}{Fore.MAGENTA}7 days before: {Style.RESET_ALL}{Fore.GREEN}{table_record['P_bef_7d']}   {Style.RESET_ALL}{Fore.MAGENTA}3 days before: {Style.RESET_ALL}{Fore.GREEN}{table_record['P_bef_3d']}   {Style.RESET_ALL}{Fore.MAGENTA}3 days after: {Style.RESET_ALL}{Fore.GREEN}{table_record['P_aft_3d']}   {Style.RESET_ALL}{Fore.MAGENTA}7 days after: {Style.RESET_ALL}{Fore.GREEN}{table_record['P_aft_7d']}   {Style.RESET_ALL}{Fore.MAGENTA}15 days after: {Style.RESET_ALL}{Fore.GREEN}{table_record['P_aft_15d']}   {Style.RESET_ALL}")
conn.close()
print('\n')
