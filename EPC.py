import requests
from bs4 import BeautifulSoup
import pymysql
from datetime import datetime
from dotenv import load_dotenv
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Load environment variables from .env file
load_dotenv()

def setup_session():
    """Create a session with retry strategy and timeout settings."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def get_form_data(url, session):
    """Extract necessary form data from the initial page load."""
    try:
        response = session.get(url, timeout=30)  # 30-second timeout
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        return {
            "__VIEWSTATE": soup.find('input', {'name': '__VIEWSTATE'})['value'],
            "__VIEWSTATEGENERATOR": soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value'],
            "__EVENTVALIDATION": soup.find('input', {'name': '__EVENTVALIDATION'})['value'],
            "ctl00$ContentSearch$txtName": "",
            "ctl00$ContentSearch$cboDistricts": "-- Any District --",
            "ctl00$ContentSearch$cmdSearch": "Search"
        }
    except requests.RequestException as e:
        print(f"Error fetching form data: {e}")
        return None

def parse_date(date_str):
    """Convert date string from MM/DD/YYYY to YYYY-MM-DD format."""
    try:
        month = date_str[0:2]
        day = date_str[3:5]
        year = date_str[6:11]
        return f"{year}-{month}-{day}"
    except (IndexError, ValueError) as e:
        print(f"Error parsing date {date_str}: {e}")
        return None

def scrape_teacher_data():
    """Scrape teacher data and store it in the database."""
    # Database connection
    try:
        conn = pymysql.connect(
            host=os.getenv("DB1_HOST"),
            user=os.getenv("DB1_USER"),
            password=os.getenv("DB1_PASSWORD"),
            database=os.getenv("DB1_NAME"),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
    except pymysql.Error as e:
        print(f"Database connection failed: {e}")
        return

    url = os.getenv('URL_EPC')
    session = setup_session()
    form_data = get_form_data(url, session)
    if not form_data:
        return

    # Insert statement
    insert_statement = """
        INSERT INTO BadTeachers2 
        (CaseNum, NameFull, Agency, Adjudication, FileDate, FileLink, FileName)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        CaseNum = VALUES(CaseNum),
        NameFull = VALUES(NameFull),
        Agency = VALUES(Agency),
        Adjudication = VALUES(Adjudication),
        FileDate = VALUES(FileDate),
        FileLink = VALUES(FileLink),
        FileName = VALUES(FileName)
    """

    try:
        # Post request with increased timeout and parse results
        response = session.post(url, data=form_data, timeout=60)  # 60-second timeout for POST
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.findAll('table')[2].findAll('tr')

        # Batch processing for better performance
        batch_size = 100
        batch_data = []
        
        # Process each row
        for row in table[1:]:
            try:
                tds = row.findAll('td')
                file_date = parse_date(tds[5].text)
                print(file_date)
                
                if file_date and file_date.startswith('2025'):
                    file_link = tds[6].find('a')['href']
                    row_data = (
                        tds[0].text,  # CaseNum
                        tds[1].text,  # NameFull
                        tds[2].text,  # Agency
                        tds[3].text,  # Adjudication
                        file_date,    # FileDate
                        file_link,    # FileLink
                        file_link.split("/")[-1]  # FileName
                    )
                    
                    batch_data.append(row_data)
                    print(f"Processing record with date: {file_date}")

                    # Execute batch when size is reached
                    if len(batch_data) >= batch_size:
                        cursor.executemany(insert_statement, batch_data)
                        conn.commit()
                        batch_data = []

            except Exception as e:
                print(f"Error processing row: {e}")
                continue

        # Insert remaining records
        if batch_data:
            cursor.executemany(insert_statement, batch_data)
            conn.commit()

    except requests.RequestException as e:
        print(f"Error during POST request: {e}")
    except pymysql.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        cursor.close()
        conn.close()
        session.close()

if __name__ == "__main__":
    scrape_teacher_data()
