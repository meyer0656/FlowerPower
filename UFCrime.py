import pymysql
import pandas as pd
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

url = os.getenv('URL_UFCRIME')

df = pd.read_json(url)
df.drop(labels=['CRIME_PERIOD','REPORT_DATE_PRETTY'], axis=1, inplace=True)

df['REPORT_DATE'] = pd.to_datetime(df['REPORT_DATE'])
df['CRIME_START'] = pd.to_datetime(df['CRIME_START'])
df['CRIME_END'] = pd.to_datetime(df['CRIME_END'])

df['REPORT_DATE'] = df['REPORT_DATE'].astype(str)
df['CRIME_START'] = df['CRIME_START'].astype(str)
df['CRIME_END'] = df['CRIME_END'].astype(str)

df.CRIME_END = df.CRIME_END.apply(lambda x : None if x=="NaT" else x)


#MYSQL LOGIN
try:
    conn = pymysql.connect(
        host = os.getenv("DB1_HOST"),
        user = os.getenv("DB1_USER"),
        password = os.getenv("DB1_PASSWORD"),
        database = os.getenv("DB1_NAME"),
        charset = 'utf8mb4',
        cursorclass = pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()
except pymysql.Error as e:
    print(f"Database connection failed: {e}")
cursor = conn.cursor()

for index, row in df.iterrows():
    try:
        print(row['CRIME_END'])
        sql = "INSERT INTO `UFCrime` (ID,AGENCY_ID,AGENCY_NAME,REPORT_NUMBER,REPORT_DATE,LOG_DATE,CRIME_TYPE,CRIME_START,CRIME_END,LOCATION,DISPOSITION_ID,DISPOSITION_DESCRIPTION,SITECODE,SITE_NAME,CRIME_TYPE_UPDATED,DISPOSITION_UPDATED,CRIME_TYPE_SUB) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE ID=values(ID), AGENCY_ID=values(AGENCY_ID), AGENCY_NAME=values(AGENCY_NAME), REPORT_NUMBER=values(REPORT_NUMBER), REPORT_DATE=values(REPORT_DATE), LOG_DATE=values(LOG_DATE), CRIME_TYPE=values(CRIME_TYPE), CRIME_START=values(CRIME_START), CRIME_END=values(CRIME_END), LOCATION=values(LOCATION), DISPOSITION_ID=values(DISPOSITION_ID), DISPOSITION_DESCRIPTION=values(DISPOSITION_DESCRIPTION), SITECODE=values(SITECODE), SITE_NAME=values(SITE_NAME), CRIME_TYPE_UPDATED=values(CRIME_TYPE_UPDATED), DISPOSITION_UPDATED=values(DISPOSITION_UPDATED), CRIME_TYPE_SUB=values(CRIME_TYPE_SUB)"
        cursor.execute(sql, (row['ID'],row['AGENCY_ID'],row['AGENCY_NAME'],row['REPORT_NUMBER'],row['REPORT_DATE'],row['LOG_DATE'],row['CRIME_TYPE'],row['CRIME_START'],row['CRIME_END'],row['LOCATION'],row['DISPOSITION_ID'],row['DISPOSITION_DESCRIPTION'],row['SITECODE'],row['SITE_NAME'],row['CRIME_TYPE_UPDATED'],row['DISPOSITION_UPDATED'],row['CRIME_TYPE_SUB']))
        conn.commit()
    except:
        continue
