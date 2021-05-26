# Import libraries
import os
import sys
sys.path.insert(1, '/scripts')
from colorama import Fore, Back, Style
import inquire as inq
import pandas as pd
import psycopg2
import AWSResourceDeploy as aws
import analysis as alys


print('\n')

# Define the region
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

# Prepare dataframes for further analysis
def analyze():

    # Ask for the dimension for analysis, by which we should study the stock returns
    analysisMessage = f"{Fore.MAGENTA}Choose one of the following criteria by which you want to perform analysis: {Style.RESET_ALL}"
    analysisOptions = [
            "a. By specific stock(s)", 
            "b. By market capitalization",
            "c. By polarity bracket",
            "d. None"
            ]
    analysisName = "criteria"
    analysisAnswer = inq.define_list(analysisName, analysisMessage, analysisOptions)
    print('\n')
    if analysisAnswer == "Nothing":
        sys.exit()

    # Ask for the polarity measure that we conduct the analysis 
    polarityMessage = f"{Fore.MAGENTA}Choose the polarity measure: {Style.RESET_ALL}"
    polarityOptions = [
            "POLARITY", 
            "AWS_POLARITY",
            "None"
            ]
    polarityName = "polarity"
    polarityAnswer = inq.define_list(polarityName, polarityMessage, polarityOptions)
    print('\n')
    if polarityAnswer == "Nothing":
        sys.exit()

    # Prepare the base dataframes across polarity extremes such as positive and negative
    positive_query = """
            SELECT SYMBOL, ARTICLE_DATE, POLARITY, AWS_POLARITY, R_at_0d, R_bef_15d, R_bef_7d, R_bef_3d, R_aft_3d, R_aft_7d, R_aft_15d 
            FROM articles
            WHERE {} BETWEEN 0 AND 1 
            AND R_at_0d IS NOT NULL AND R_bef_15d IS NOT NULL AND R_bef_7d IS NOT NULL AND R_bef_3d IS NOT NULL AND R_aft_3d IS NOT NULL AND R_aft_7d IS NOT NULL AND R_aft_15d IS NOT NULL
            ORDER BY ARTICLE_DATE DESC""".format(polarityAnswer)
    negative_query = """
            SELECT SYMBOL, ARTICLE_DATE, POLARITY, AWS_POLARITY, R_at_0d, R_bef_15d, R_bef_7d, R_bef_3d, R_aft_3d, R_aft_7d, R_aft_15d 
            FROM articles
            WHERE {} < 0
            AND R_at_0d IS NOT NULL AND R_bef_15d IS NOT NULL AND R_bef_7d IS NOT NULL AND R_bef_3d IS NOT NULL AND R_aft_3d IS NOT NULL AND R_aft_7d IS NOT NULL AND R_aft_15d IS NOT NULL
            ORDER BY ARTICLE_DATE DESC""".format(polarityAnswer)

    polarityAnswer = polarityAnswer.lower()
    base_positive_df = pd.read_sql_query(positive_query, conn)
    base_negative_df = pd.read_sql_query(negative_query, conn)

    # Add the bin column to the dataframes
    base_positive_df['polarity_cut']= pd.cut(base_positive_df[polarityAnswer], bins = 4, labels = [0, 1, 2, 3], include_lowest=True)
    base_negative_df['polarity_cut']= pd.cut(base_negative_df[polarityAnswer], bins = 4, labels = [0, 1, 2, 3], include_lowest=True)

    # Save as a csv file locally
    base_positive_df.to_csv('returns-positive_' + polarityAnswer + '.csv', index=False)
    base_negative_df.to_csv('returns-negative_' + polarityAnswer + '.csv', index=False)

    # Adjust the base data frames according to the dimension
    if analysisAnswer[0] == "a":
        selectStockMessage = f"{Fore.MAGENTA}Enter symbols of the stocks you are interested in and separate them by commas, e.g. AAPL, GOOGL, XELA, FB:{Style.RESET_ALL} {Fore.YELLOW}"
        selected_stock_list = input(selectStockMessage).replace(" ", "").split(",")
        {Style.RESET_ALL}

        # Get the dataframes of selected stocks
        mask = base_positive_df["symbol"].isin(selected_stock_list)
        selected_stocks_positive_df = base_positive_df[mask]
        selected_stocks_negative_df = base_negative_df[mask]

        # Create dataframes by binning
        polarity_group_0_positive_df = selected_stocks_positive_df[selected_stocks_positive_df['polarity_cut'] == 0]
        polarity_group_1_positive_df = selected_stocks_positive_df[selected_stocks_positive_df['polarity_cut'] == 1]
        polarity_group_2_positive_df = selected_stocks_positive_df[selected_stocks_positive_df['polarity_cut'] == 2]
        polarity_group_3_positive_df = selected_stocks_positive_df[selected_stocks_positive_df['polarity_cut'] == 3]

        polarity_group_0_negative_df = selected_stocks_negative_df[selected_stocks_negative_df['polarity_cut'] == 0]
        polarity_group_1_negative_df = selected_stocks_negative_df[selected_stocks_negative_df['polarity_cut'] == 1]
        polarity_group_2_negative_df = selected_stocks_negative_df[selected_stocks_negative_df['polarity_cut'] == 2]
        polarity_group_3_negative_df = selected_stocks_negative_df[selected_stocks_negative_df['polarity_cut'] == 3]

        # Plot parameters
        title = "Stock Return Change of Selected Stocks over a Time Period across Different Polarity Score Segments"
        plotName = 'selected_stock_returns_across_polarity' + '.png'
        positive_list = [selected_stocks_positive_df, polarity_group_0_positive_df, polarity_group_1_positive_df, polarity_group_2_positive_df, polarity_group_3_positive_df]
        negative_list = [selected_stocks_negative_df, polarity_group_0_negative_df, polarity_group_1_negative_df, polarity_group_2_negative_df, polarity_group_3_negative_df]
        alys.plot_data(positive_list, negative_list, title, plotName)

        # Correlation analysis parameters
        description = "correlations between returns of selected stocks before and after the article date across different polarity score segments"
        correlation_keys = alys.calculate_correlation(positive_list, negative_list, description)

        # Regression analysis and risk assessment
        dfs = {'positive_polarity': selected_stocks_positive_df, 'negative_polarity': selected_stocks_negative_df}
        alys.assess_risk(correlation_keys, dfs)

    elif analysisAnswer[0] == "b":
        print(f"{Fore.MAGENTA}Results will be submitted by binning market capitalization.{Style.RESET_ALL}")
        q = "SELECT * FROM stocks ORDER BY SYMBOL ASC"
        market_cap_df = pd.read_sql_query(q, conn)

        # Get dataframes by bins of market capitalization
        market_cap_df['market_cap_cut'] = pd.cut(market_cap_df['market_cap'], bins=4, labels = [0, 1, 2, 3], include_lowest=True)

        # Merge the 'stocks' dataframe with each of the base dataframes produced from 'articles' data
        left_merged_positive_df = pd.merge(base_positive_df, market_cap_df, how="left", on="symbol", sort=True)
        left_merged_negative_df = pd.merge(base_negative_df, market_cap_df, how="left", on="symbol", sort=True)

        # Create dataframes by binning
        market_cap_group_0_positive_df = left_merged_positive_df[left_merged_positive_df['market_cap_cut'] == 0]
        market_cap_group_1_positive_df = left_merged_positive_df[left_merged_positive_df['market_cap_cut'] == 1]
        market_cap_group_2_positive_df = left_merged_positive_df[left_merged_positive_df['market_cap_cut'] == 2]
        market_cap_group_3_positive_df = left_merged_positive_df[left_merged_positive_df['market_cap_cut'] == 3]

        market_cap_group_0_negative_df = left_merged_negative_df[left_merged_negative_df['market_cap_cut'] == 0]
        market_cap_group_1_negative_df = left_merged_negative_df[left_merged_negative_df['market_cap_cut'] == 1]
        market_cap_group_2_negative_df = left_merged_negative_df[left_merged_negative_df['market_cap_cut'] == 2]
        market_cap_group_3_negative_df = left_merged_negative_df[left_merged_negative_df['market_cap_cut'] == 3]

        # Plot parameters
        title = "Stock Return Change of All Stocks over a Time Period across Different Market Capitalization Segments"
        plotName = 'all_stock_returns_across_market_cap' + '.png'
        positive_list = [left_merged_positive_df, market_cap_group_0_positive_df, market_cap_group_1_positive_df, market_cap_group_2_positive_df, market_cap_group_3_positive_df]
        negative_list = [left_merged_negative_df, market_cap_group_0_negative_df, market_cap_group_1_negative_df, market_cap_group_2_negative_df, market_cap_group_3_negative_df]
        alys.plot_data(positive_list, negative_list, title, plotName)

        # Correlation analysis parameters
        description = "correlations between returns of all stocks before and after the article date across different market capitalization segments"
        correlation_keys = alys.calculate_correlation(positive_list, negative_list, description)

        # Regression analysis and risk assessment
        dfs = {'positive_polarity': left_merged_positive_df, 'negative_polarity': left_merged_negative_df}
        alys.assess_risk(correlation_keys, dfs)

    # Get dataframes by bins of polarity
    elif analysisAnswer[0] == "c":
        print(f"{Fore.MAGENTA}Results will be submitted by binning polarity scores.{Style.RESET_ALL}")

        # Create dataframes by binning
        polarity_group_0_positive_df = base_positive_df[base_positive_df['polarity_cut'] == 0]
        polarity_group_1_positive_df = base_positive_df[base_positive_df['polarity_cut'] == 1]
        polarity_group_2_positive_df = base_positive_df[base_positive_df['polarity_cut'] == 2]
        polarity_group_3_positive_df = base_positive_df[base_positive_df['polarity_cut'] == 3]

        polarity_group_0_negative_df = base_negative_df[base_negative_df['polarity_cut'] == 0]
        polarity_group_1_negative_df = base_negative_df[base_negative_df['polarity_cut'] == 1]
        polarity_group_2_negative_df = base_negative_df[base_negative_df['polarity_cut'] == 2]
        polarity_group_3_negative_df = base_negative_df[base_negative_df['polarity_cut'] == 3]

        # Plot parameters
        title = "Stock Return Change of All Stocks over a Time Period across Different Polarity Score Segments"
        plotName = 'all_stock_returns_across_polarity' + '.png'
        positive_list = [base_positive_df, polarity_group_0_positive_df, polarity_group_1_positive_df, polarity_group_2_positive_df, polarity_group_3_positive_df]
        negative_list = [base_negative_df, polarity_group_0_negative_df, polarity_group_1_negative_df, polarity_group_2_negative_df, polarity_group_3_negative_df]
        alys.plot_data(positive_list, negative_list, title, plotName)

        # Correlation analysis parameters
        description = "correlations between returns of all stocks before and after the article date across different polarity score segments"
        correlation_keys = alys.calculate_correlation(positive_list, negative_list, description)

        # Regression analysis and risk assessment
        dfs = {'positive_polarity': base_positive_df, 'negative_polarity': base_negative_df}
        alys.assess_risk(correlation_keys, dfs)

    else:
        sys.exit()
        
    print('\n')

selectionMessage = f"{Fore.MAGENTA}Choose one of the following operations to perform: {Style.RESET_ALL}"
options = [
        "a. Create an RDS instance and a database", 
        "b. Create an EC2 instance to run the scripts and write to the database",
        "c. Create a database table, an S3 bucket and import the data from S3 to the table", 
        "d. Get news articles' links from MarketWatch",
        "e. Find polarity and/or AWS Comprehend sentiment scores",
        "f. Find the stock prices on, before and after the news article date",
        "g. Calculate the stock returns before and after the news article date",
        "h. Perform correlation and regression analyses, and plot graphs",
        "i. None"
        ]

name = "menu"
answer = inq.define_list(name, selectionMessage, options)
print('\n')

if answer[0] == "a":
    os.system('python3 b_deploy_aws_resources-I.py')
elif answer[0] == "b":
    os.system('python3 c_deploy_aws_resources-II.py')
elif answer[0] == "c":
    os.system('python3 d_import_s3_to_rds.py')
elif answer[0] == "d":
    os.system('python3 e_query.py')
elif answer[0] == "e":
    os.system('python3 g_polarity_finder.py')
elif answer[0] == "f":
    os.system('python3 h_price_finder.py')
elif answer[0] == "g":
    os.system('python3 i_return_calculator.py')
elif answer[0] == "h":
    analyze()
else:
    sys.exit()
