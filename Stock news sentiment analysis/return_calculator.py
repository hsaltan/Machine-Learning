# Import libraries
import sys
sys.path.insert(1, '/scripts')
from colorama import Fore, Back, Style
import AWSResourceDeploy as aws
import psycopg2


# Define the region and boto3 clients
region = "eu-west-1"

# Prices and returns
dates = ["P_at_0d", "P_bef_15d", "P_bef_7d", "P_bef_3d", "P_aft_3d", "P_aft_7d", "P_aft_15d"]
returns = ["R_at_0d", "R_bef_15d", "R_bef_7d", "R_bef_3d", "R_aft_3d", "R_aft_7d", "R_aft_15d"]
lower_returns = [r.lower() for r in returns]

# Database credentials
dbiParamName = "dbInstanceIdentifier"
userPasswordParamName = "masterUserPassword"
dbInstanceIdentifier = aws.get_parameter(dbiParamName, region)
masterUserPassword = aws.get_parameter(userPasswordParamName, region)
endpoint, port, usr, dbName = aws.describe_rds(dbInstanceIdentifier, region)

# Open the database connection
conn = psycopg2.connect(host=endpoint, port=port, database=dbName, user=usr, password=masterUserPassword)
cur = conn.cursor()

# Calculate returns
def calculate_returns():
    for item in range(0, 4):
        articleDatePrice = dates[0]
        targetDatePrice = dates[item]
        targetDateReturn = returns[item]
        q = """
        UPDATE articles SET {a} = ROUND((({b} - {c}) / {b} * 100),2) WHERE 
        P_at_0d IS NOT NULL AND P_at_0d <> 0 AND {a} IS NULL AND {c} IS NOT NULL AND {c} <> 0
        """.format(a=targetDateReturn, b=articleDatePrice , c=targetDatePrice)
        cur.execute(q)
        conn.commit()

    for item in range(4, 7):
        articleDatePrice = dates[0]
        targetDatePrice = dates[item]
        targetDateReturn = returns[item]
        q = """
        UPDATE articles SET {a} = ROUND((({b} - {c}) / {c} * 100),2) WHERE 
        P_at_0d IS NOT NULL AND P_at_0d <> 0 AND {a} IS NULL AND {b} IS NOT NULL AND {b} <> 0
        """.format(a=targetDateReturn, b=targetDatePrice , c=articleDatePrice)
        cur.execute(q)
        conn.commit()

calculate_returns()

print(f"{Fore.MAGENTA}Returns on available prices have been calculated and written to the database.{Style.RESET_ALL}")
print('\n')

# Upload the data table 'articles' to S3 (just in case)?
answer = input(f"{Fore.MAGENTA}Should the articles table be uploaded to S3 (Y/n)?: {Style.RESET_ALL}{Fore.YELLOW}")
if answer == "Y" or answer == "y":
    bucket = input(f"{Fore.MAGENTA}Enter the bucket name: {Style.RESET_ALL}{Fore.YELLOW}")
    fileName = 'news_articles_data.csv'
    cur.execute("SELECT * FROM aws_s3.query_export_to_s3('SELECT * FROM articles', aws_commons.create_s3_uri({a}, {b}, {c}), options :='format csv, delimiter $$,$$')".format(a=bucket, b=fileName, c=region))
{Style.RESET_ALL}
print('\n')
