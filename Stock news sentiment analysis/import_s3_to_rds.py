# Import libraries
import sys
sys.path.insert(1, 'YOUR_PATH_TO_AWSResourceDeploy_SCRIPT_ON_YOUR_LOCAL_MACHINE')
import AWSResourceDeploy as aws
from colorama import Fore, Back, Style
from datetime import datetime
import psycopg2


# Define the region and boto3 clients
region = "eu-west-1"

# Files to copy
files = ['amex.csv', 'nasdaq.csv', 'nyse.csv']

# Chosen stock lists
stock_list = {
'DOW30' : ['AXP', 'AMGN', 'AAPL', 'BA', 'CAT', 'CSCO', 'CVX', 'GS', 'HD', 'HON', 'IBM', 'INTC',
           'JNJ', 'KO', 'JPM', 'MCD', 'MMM', 'MRK', 'MSFT', 'NKE', 'PG', 'TRV', 'UNH', 'CRM',
           'VZ', 'V', 'WBA', 'WMT', 'DIS', 'DOW'],
'SP100' : ['AAPL', 'ABBV', 'ABT', 'ACN', 'ADBE', 'AIG', 'ALL', 'AMGN', 'AMT', 'AMZN', 'AXP', 'BA',
           'BAC', 'BIIB', 'BK', 'BKNG', 'BLK', 'BMY', 'BRK.B', 'C', 'CAT', 'CHTR', 'CL', 'CMCSA',
           'COF', 'COP', 'COST', 'CRM', 'CSCO', 'CVS', 'CVX', 'DD', 'DHR', 'DIS', 'DOW', 'DUK',
           'EMR', 'EXC', 'F', 'FB', 'FDX', 'GD', 'GE', 'GILD', 'GM', 'GOOG', 'GOOGL', 'GS', 'HD',
           'HON', 'IBM', 'INTC', 'JNJ', 'JPM', 'KHC', 'KMI', 'KO', 'LLY', 'LMT', 'LOW', 'MA', 'MCD',
           'MDLZ','MDT', 'MET', 'MMM', 'MO', 'MRK', 'MS', 'MSFT', 'NEE', 'NFLX', 'NKE', 'NVDA','ORCL',
           'PEP', 'PFE', 'PG', 'PM', 'PYPL', 'QCOM', 'RTX', 'SBUX', 'SLB', 'SO', 'SPG', 'T', 'TGT',
           'TMO', 'TSLA', 'TXN', 'UNH', 'UNP', 'UPS', 'USB', 'V', 'VZ', 'WBA', 'WFC', 'WMT', 'XOM'],
'NASDAQ100' : ['ATVI', 'ATVI', 'AMD', 'ADBE', 'ALGN', 'ALXN', 'AMZN', 'AMGN', 'AEP', 'ADI', 'ANSS', 
               'AAPL', 'AMAT', 'ASML', 'TEAM', 'ADSK', 'ADP', 'AVGO', 'BIDU', 'BIIB', 'BMRN', 'BKNG', 
               'CDNS', 'CDW', 'CERN', 'CHKP', 'CHTR', 'CPRT', 'CTAS', 'CSCO', 'CMCSA', 'COST', 'CSX', 
               'CTSH', 'DOCU', 'DXCM', 'DLTR', 'EA', 'EBAY', 'EXC', 'FAST', 'FB', 'FISV', 'FOX', 
               'FOXA', 'GILD', 'GOOG', 'GOOGL', 'ILMN', 'INCY', 'INTC', 'INTU', 'ISRG', 'MRVL', 
               'IDXX', 'JD', 'KDP', 'KLAC', 'KHC', 'LRCX', 'LULU', 'MELI', 'MAR', 'MTCH', 'MCHP', 
               'MDLZ', 'MRNA', 'MNST', 'MSFT', 'MU', 'MXIM', 'NFLX', 'NTES', 'NVDA', 'NXPI', 'OKTA', 
               'ORLY', 'PAYX', 'PCAR', 'PDD', 'PTON', 'PYPL', 'PEP', 'QCOM', 'REGN', 'ROST', 'SIRI', 
               'SGEN', 'SPLK', 'SWKS', 'SBUX', 'SNPS', 'TCOM', 'TSLA', 'TXN', 'TMUS', 'VRSN', 'VRSK', 
               'VRTX', 'WBA', 'WDAY', 'XEL', 'XLNX', 'ZM']
}

# Database credentials
dbiParamName = "dbInstanceIdentifier"
userPasswordParamName = "masterUserPassword"
dbInstanceIdentifier = aws.get_parameter(dbiParamName, region)
masterUserPassword = aws.get_parameter(userPasswordParamName, region)
endpoint, port, usr, dbName = aws.describe_rds(dbInstanceIdentifier, region)

# Create an S3 bucket
def create_s3_bucket():
    now = datetime.now()
    dt_string = now.strftime("%Y-%b-%d-%H-%M-%S")
    bucketName = "s3b-" + dt_string.lower()
    aws.create_bucket(bucketName, region)
    return bucketName

# Upload files to S3
def upload_files():
    bucketName = create_s3_bucket()
    for file in files:
        path = "YOUR_PATH_TO_files/"
        body = path + file
        key = 'NAME'
        value = 'stock news data'
        aws.put_object(body, bucketName, file, key, value, region)
    return bucketName

# Create RDS database tables
def create_rds_table(conn, cur):
    q1 = "CREATE TABLE {} (SYMBOL varchar(10), NAME varchar(400), LAST_SALE money, NET_CHANGE varchar(10), PER_CHANGE varchar(10), MARKET_CAP decimal(15,2), COUNTRY varchar(50), IPO_YEAR integer, VOLUME integer, SECTOR varchar(100), INDUSTRY varchar(150))"
    q2 = "CREATE TABLE {} (ARTICLE_ID serial PRIMARY KEY, SYMBOL varchar(10), LINK varchar(1000), ARTICLE_DATE date, POLARITY numeric(4, 3), AWS_POLARITY numeric(4, 3), P_at_0d numeric(7, 2), P_bef_15d numeric(7, 2), P_bef_7d numeric(7, 2), P_bef_3d numeric(7, 2), P_aft_3d numeric(7, 2), P_aft_7d numeric(7, 2), P_aft_15d numeric(7, 2), R_at_0d numeric(5, 2), R_bef_15d numeric(5, 2), R_bef_7d numeric(5, 2), R_bef_3d numeric(5, 2), R_aft_3d numeric(5, 2), R_aft_7d numeric(5, 2), R_aft_15d numeric(5, 2))"
    db_tables = [('stocks', q1), ('articles', q2)]
    for db_table in db_tables:
        try:
            cur.execute(db_table[1].format(db_table[0]))
            conn.commit()
        except Exception as e:
            print("Database connection failed due to {}".format(e))
    dbTableName = db_tables[0][0]

    # Add new columns to the table
    cur.execute('ALTER TABLE {} ADD COLUMN STOCK_EXC varchar(10), ADD COLUMN DOW30 varchar(10), ADD COLUMN SP100 varchar(10), ADD COLUMN NASDAQ100 varchar(10)'.format(dbTableName))
    conn.commit()
    return db_tables, dbTableName

# Import data from S3 to RDS table
def import_data_to_rds(conn, cur, dbTableName, bucketName):

    # Import data from S3 to RDS
    for file in files:
        cur.execute("SELECT aws_s3.table_import_from_s3('{a}', 'SYMBOL, NAME, LAST_SALE, NET_CHANGE, PER_CHANGE, MARKET_CAP, COUNTRY, IPO_YEAR, VOLUME, SECTOR, INDUSTRY', '(format csv, header true)', aws_commons.create_s3_uri('{b}', '{c}', '{d}'))".format(a=dbTableName, b=bucketName, c=file, d=region))
        conn.commit()

        # Add the stock exchange names to the new columns
        seName = file.replace(".csv", "").upper()
        cur.execute("UPDATE stocks SET STOCK_EXC='{}' WHERE STOCK_EXC IS NULL".format(seName))
        conn.commit()

    # Add index names to the new columns
    for key, value in stock_list.items():
        for item in value:
            cur.execute("UPDATE {a} SET {b} = 'Yes' WHERE SYMBOL = '{c}'".format(a=dbTableName, b=key, c=item))
            conn.commit()

    # Drop unneccessary columns
    cur.execute("ALTER TABLE stocks DROP COLUMN LAST_SALE, DROP COLUMN NET_CHANGE, DROP COLUMN PER_CHANGE, DROP COLUMN VOLUME")
    conn.commit()

# Create the extension
def create_extension():
    conn = psycopg2.connect(host=endpoint, port=port, database=dbName, user=usr, password=masterUserPassword)
    cur = conn.cursor()
    cur.execute('CREATE EXTENSION aws_s3 CASCADE')
    conn.commit()
    bucketName = upload_files()
    print('\n')
    print(f"{Fore.MAGENTA}Bucket{Style.RESET_ALL} {Fore.CYAN}{bucketName}{Style.RESET_ALL} {Fore.MAGENTA}has been created and the files{Style.RESET_ALL} {Fore.CYAN}{files[0], files[1], files[2]}{Style.RESET_ALL} {Fore.MAGENTA}have been uploaded successfully.{Style.RESET_ALL}")
    print('\n')
    db_tables, dbTableName = create_rds_table(conn, cur)
    print(f"{Fore.MAGENTA}Database tables{Style.RESET_ALL} {Fore.CYAN}{db_tables[0][0]}{Style.RESET_ALL} {Fore.MAGENTA}and{Style.RESET_ALL} {Fore.CYAN}{db_tables[1][0]}{Style.RESET_ALL} {Fore.MAGENTA}have been successfully created.{Style.RESET_ALL}")
    print('\n')
    import_data_to_rds(conn, cur, dbTableName, bucketName)
    print(f"{Fore.MAGENTA}Files in the bucket have been successfully imported to the database tables.{Style.RESET_ALL}")
    print('\n')
    conn.close()

create_extension()
