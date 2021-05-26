# Import libraries
from bs4 import BeautifulSoup 
import requests
import psycopg2
import dateutil.parser as p
from colorama import Fore, Back, Style


# Insert the results to the database
def insert_datatable(numberOfLinks, selected_ticker, filtered_links_with_dates, conn, cur):
    if filtered_links_with_dates:
        for link in filtered_links_with_dates:
            cur.execute("INSERT INTO articles (SYMBOL, LINK, ARTICLE_DATE) VALUES ('{a}', '{b}', '{c}')".format(a=selected_ticker, b=link[0], c=link[1]))
            conn.commit()
            print(f"{Fore.RED}{numberOfLinks}.{Style.RESET_ALL}\t{Fore.CYAN}{link[1]}{Style.RESET_ALL}\t{Fore.GREEN}{link[0]}{Style.RESET_ALL}")
            numberOfLinks += 1
    else:
        print(f"{Fore.GREEN}No links have been found in the date range given{Style.RESET_ALL}")
    print('\n')

# Filter out any irrelevant article based on dates
def extract_date(x, dateToBegin, dateToEnd):
    if x[1] >= dateToBegin and x[1] <= dateToEnd:
        return x

# Scrape the web pages and get the links
def get_news(dateToBegin, dateToEnd, endpoint, port, dbName, usr, masterUserPassword, selected_tickers):

    # Get the year, month and day of the ending date in the query
    endingDate = dateToEnd.strftime('%Y-%m-%d').split("-")
    year = endingDate[0]
    month = endingDate[1]
    day = endingDate[2]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

    # Open database connection
    conn = psycopg2.connect(host=endpoint, port=port, database=dbName, user=usr, password=masterUserPassword)
    cur = conn.cursor()

    # Scrape article links and dates
    for selected_ticker in selected_tickers:
        print('\n')
        print(f"{Fore.MAGENTA}The following links have been collected and written to the database for{Style.RESET_ALL} {Fore.CYAN}{selected_ticker}: {Style.RESET_ALL}")
        print('\n')

        # Find the url of the page of the ending date
        base_url = "https://www.marketwatch.com/search?q="+selected_ticker+"&m=Ticker&rpp=100&mp=2005&bd=true&bd=false&bdv="+month+"%2F"+day+"%2F"+year+"&rs=true"
        page = 1
        nav = "Next"
        numberOfLinks = 1

        # Keep crawling for more pages
        while nav == "Next":
            if page > 1:
                new_page = "&o="+str(page)
            else:
                new_page = ""

            # Scrape the target page
            active_url = base_url + new_page
            r = requests.get(active_url, headers=headers)
            c = r.content
            soup = BeautifulSoup(c, "html.parser")
            
            # Find all results with the article links and dates
            try:
                resultlist = soup.findAll('div', attrs={'class' : 'resultlist'})[0]
            except:
                break

            # Extract the links
            search_results = resultlist.findAll('div', attrs={'class' : 'searchresult'})
            links = [x.find('a')['href'] for x in search_results]

            # Extract the dates
            dates_and_times = resultlist.findAll('div', attrs={'class' : 'deemphasized'})
            dates_extracted = [x.find('span').text.split("m")[-1].replace(".", "").lstrip() for x in dates_and_times]
            article_dates = [p.parse(x).date() for x in dates_extracted]

            # Merge links and dates
            links_with_dates = list(zip(links, article_dates))

            # Filter out any links that the dates are outside the query range
            filtered_links_with_dates = list(filter(None, [extract_date(x, dateToBegin, dateToEnd) for x in links_with_dates]))
            
            # Insert the results to the database
            insert_datatable(numberOfLinks, selected_ticker, filtered_links_with_dates, conn, cur)

            # Check if the next page is relevant
            numberOfRelevantArticles = len(filtered_links_with_dates)
            if numberOfRelevantArticles == 100:
                try:
                    nav_links = soup.findAll('div', attrs={'class' : 'nextprevlinks'})
                    for nav_link in nav_links:
                        if "Next" in nav_link.text:
                            nav = "Next"
                            page += 100
                            numberOfLinks += 100
                            break
                except:
                    nav = ""
            else:
                nav = ""
