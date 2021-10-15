This program is to see if sentiment scores of any news articles from _MarketWatch_ (https://www.marketwatch.com/) for selected stocks affect their prices. Though the analysis has been made for the _MarketWatch_, one could repeat it for any other financial website that has article links.

Program uses AWS resources, python, SQL, text analysis, visualization, web scraping, correlation and regression analysis. It first builds EC2 and RDS, then populates RDS by web scraping to find URLs, calculating sentiment scores, finding stock prices and returns, and finally performs analyses and plots the data. The whole process is managed by `main.py` file which has a menu that enables the process to be done partially at different times.

Deployment of AWS resources and importing stocks list data to RDS are done on the local machine for one time only, and the later data entry and analyses can be performed on EC2 by calling the main.py script. Since `AWSResourceDeploy.py` and `inquire.py` are common programs that can be used for other projects, I put them in __AWS Projects__ and __Python Applications__ folders respectively. The current program needs them to run.

Program can generally be run as in the order below. However, after the deployment of AWS resources and importing the data to RDS (2,3,4), the following scripts may not follow the order exactly depending on the type of missing data (links, sentiment scores, prices, or returns):
  1. `main.py`
  2. `deploy_aws_resources-I.py`
  3. `deploy_aws_resources-II.py`
  4. `import_s3_to_rds.py`
  5. `query.py`
  6. `link_finder.py`
  7. `polarity_finder.py`
  8. `price_finder.py`
  9. `return_calculator.py`
  10. `analysis.py`

Once all script files are imported to EC2 `/scripts` folder, they are ready to run on EC2.
