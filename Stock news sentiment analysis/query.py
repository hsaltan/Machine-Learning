# Import libraries
import sys
sys.path.insert(1, '/scripts')
from colorama import Fore, Back, Style
import inquire as inq
import AWSResourceDeploy as aws
from datetime import datetime, timedelta
import dateutil.parser as p
import link_finder as lf
import psycopg2
import random


# Define the region
region = "eu-west-1"

# Database credentials
dbiParamName = "dbInstanceIdentifier"
userPasswordParamName = "masterUserPassword"
dbInstanceIdentifier = aws.get_parameter(dbiParamName, region)
masterUserPassword = aws.get_parameter(userPasswordParamName, region)
endpoint, port, usr, dbName = aws.describe_rds(dbInstanceIdentifier, region)

# Connect to the database
conn = psycopg2.connect(host=endpoint, port=port, database=dbName, user=usr, password=masterUserPassword)
cur = conn.cursor()

# Stock lists
stock_list_names = ['NYSE', 'AMEX', 'NASDAQ', 'DOW30', 'SP100', 'NASDAQ100', 'ALL STOCKS']

class DateError(Exception):
    """Raised when the input date value is not within the permissible range"""

    def __init__(self, message=f"{Fore.RED}You have entered a wrong date!{Style.RESET_ALL}"):
        self.message = message
        print('\n')
        print(self.message)
        print('\n')

# Choose target stock list(s)
def choose_target_stocks(stockExchangeMessage):
    name = "stock_exchange"
    selected_stock_list = inq.define_list(name, stockExchangeMessage, stock_list_names)
    print('\n')
    return selected_stock_list

# Choose the method to select the target stocks
def select_stocks():
    selectionMessage = f"{Fore.MAGENTA}How do you want to select stocks?: {Style.RESET_ALL}"
    options = [
            'a. I want to select all stocks listed on (a) particular stock exchange(s)', 
            'b. I want to select a randomly chosen subset of stocks listed on (a) particular stock exchange(s)', 
            'c. I want to enter stock symbols myself'
            ]

    name = "stock_selection_method"
    stockSelectionMethod = inq.define_list(name, selectionMessage, options)
    print('\n')

    # Stock exchange selection
    stocksSubset = 0
    if stockSelectionMethod[0] == 'a':
        stockExchangeMessage = f"{Fore.MAGENTA}Below choose a stock list. All stocks in the list will be considered.{Style.RESET_ALL}"
        selected_stock_list = choose_target_stocks(stockExchangeMessage)
        print(f"{Fore.RED}Stocks that the news will be collected for are from{Style.RESET_ALL} {Fore.CYAN}{selected_stock_list}{Style.RESET_ALL}")

    # Random number of stock selection from any stock exchange
    elif stockSelectionMethod[0] == 'b':
        stocksSubset = int(input(f"{Fore.MAGENTA}Enter the number of stocks you want randomly selected: {Style.RESET_ALL}"))
        print('\n')
        stockExchangeMessage = f"{Fore.MAGENTA}Below choose a stock list from which you want the subset to be sampled: {Style.RESET_ALL}"
        selected_stock_list = choose_target_stocks(stockExchangeMessage)
        print(f"{Fore.RED}Randomly selected stocks that the news will be collected for are from{Style.RESET_ALL} {Fore.CYAN}{selected_stock_list}{Style.RESET_ALL}")

    # Select certain stocks by their tickers
    elif stockSelectionMethod[0] == 'c':
        selectStockMessage = f"{Fore.MAGENTA}Enter symbols of the stocks you are interested in and separate them by commas, e.g. AAPL, GOOGL, XELA, FB:{Style.RESET_ALL} {Fore.YELLOW}"
        {Style.RESET_ALL}
        selected_stock_list = input(selectStockMessage).replace(" ", "").split(",")
    print('\n')
    return selected_stock_list, stocksSubset

# Collect selected stocks and save them in a temporary table
def get_tickers_list():
    selected_stock_list, stocksSubset = select_stocks()

    dbTableName = 'stocks'

    # If stocks are selected by specifying their tickers
    if selected_stock_list not in stock_list_names:
        selected_tickers = selected_stock_list
    else:

        # If stocks are selected from a stock exchange randomly or a whole stock exchange is selected
        # 'DOW30', 'SP100', 'NASDAQ100' are the target markets
        if selected_stock_list in stock_list_names[3:6]:
            searchQuery = 'Yes'
            targetColumn = selected_stock_list
            q3 = "CREATE TEMPORARY TABLE tickers AS SELECT SYMBOL FROM {a} WHERE {b} = '{c}'".format(a=dbTableName, b=targetColumn, c=searchQuery)

        # 'NYSE', 'AMEX', 'NASDAQ' are the target markets
        elif selected_stock_list in stock_list_names[0:3]:
            searchQuery = selected_stock_list
            targetColumn = 'STOCK_EXC'
            q3 = "CREATE TEMPORARY TABLE tickers AS SELECT SYMBOL FROM {a} WHERE {b} = '{c}'".format(a=dbTableName, b=targetColumn, c=searchQuery)

        # 'ALL STOCKS' is the target market
        elif selected_stock_list in stock_list_names[6]:
            q3 = "CREATE TEMPORARY TABLE tickers AS SELECT SYMBOL FROM {}".format(dbTableName)

        # Creation of a temporary table, writing of results in it and assigning them to a variable 
        cur.execute(q3)
        cur.execute('SELECT * FROM tickers')
        query_results = cur.fetchall()

        # Checks if a random subset selection will occur
        # No random subset selection
        if stocksSubset == 0:
            selected_tickers = [z[0] for z in query_results]

        # Random subset selection
        else:
            selected_tickers = random.sample([z[0] for z in query_results], stocksSubset)
        del query_results[:]
    return selected_tickers

# Find today's date
today = datetime.today().date()
finalDate = today - timedelta(days=15)
thresholdDate = finalDate.strftime('%Y-%m-%d')

# Enter the dates between which you'd like to see the news about the stock(s)
# The last date of the news article
print('\n')
endingDate = input(f"{Fore.MAGENTA}Enter the date of the last news article in the format of YYYY-MM-DD, e.g. 2021-03-14.\n\nThe date you will enter should be before{Style.RESET_ALL} {Fore.GREEN}{thresholdDate}:{Style.RESET_ALL} {Fore.YELLOW}")
{Style.RESET_ALL}
dateToEnd = p.parse(endingDate).date()
print('\n')
if dateToEnd > finalDate:
    raise DateError()
else:
    # The first date of the news article
    beginningDate = input(f"{Fore.MAGENTA}Enter the date of the first news article in the format of YYYY-MM-DD, e.g. 2021-03-14.\n\nThe date you will enter should be before{Style.RESET_ALL} {Fore.GREEN}{endingDate}{Style.RESET_ALL}:{Style.RESET_ALL} {Fore.YELLOW}")
    {Style.RESET_ALL}
    dateToBegin = p.parse(beginningDate).date()
    print('\n')
    if dateToBegin > dateToEnd:
        raise DateError()

# Find the selected stocks and time frame
selected_tickers = get_tickers_list()
lf.get_news(dateToBegin, dateToEnd, endpoint, port, dbName, usr, masterUserPassword, selected_tickers)
conn.close()
print('\n')
