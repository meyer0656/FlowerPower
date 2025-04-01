from bs4 import BeautifulSoup
import requests
import re
import datetime
from datetime import date
import pymysql
import urllib.request
import json
import pandas as pd
import os
import pysftp

# GRANT CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, SELECT, REFERENCES, RELOAD on *.* TO 'mugshots'@'0.0.0.0' WITH GRANT OPTION;

# MYSQL LOGIN
conn = pymysql.connect(host='fladata.com', user='admin',
                       password='B@tteaux2@', db='FlaData')
cur = conn.cursor()

county = 'ALA'

url = 'http://asosite.alachuasheriff.org/ASOInmateViewAll.aspx'

headers = {"Connection": "keep-alive",
           "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"}

html = requests.post(url, headers=headers)
soup = BeautifulSoup(html.content, features="html.parser")
trs = soup.findAll('tr')
coun = 0
# print(soup)
with pysftp.Connection('fladata.com', username='root', password='B@tteaux2@') as sftp:
    for tr in trs[1:]:
        # print(coun)
        coun = coun + 1
        # PROFILE LINK
        url2 = tr.find('a')
        url2 = url2['href']
        print(url2)

        # NAME COMPONENTS
        fields = tr.findAll('td')
        lastname = fields[0].text
        # print(lastname)
        firstname = fields[1].text
        middlename = fields[2].text
        name = fields[3].text

        # ARREST DATE
        arrestdate = fields[4].text
        arrestdate = datetime.datetime.strptime(
        arrestdate, "%m/%d/%Y %H:%M").strftime("%Y-%m-%d %H:%M:%S")
        bookingwrapper = datetime.datetime.strptime(
        arrestdate, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d")
        #     print(bookingwrapper)

        # DEMOS
        race = fields[5].text
        sex = fields[6].text
        age = fields[7].text
        pod = fields[8].text
        agency = ''
        # print(name,lastname,firstname,middlename,arrestdate,race,sex,age,pod)

        html2 = requests.post(url2, headers=headers)
        soup2 = BeautifulSoup(html2.content, features="html.parser")
        #     print(soup2)
        inmateid = trs2 = soup2.select(
        '#GridView1 > tr:nth-child(2) > td:nth-child(2)')
        inmateid = inmateid[0].text
        bookingnumber = 'ALA-' + bookingwrapper + '-' + inmateid

        # # Download image
        image = 'ALA-' + inmateid + '.jpg'
        path = "/Users/brandon.meyer/Desktop/Python2/Mugshots/images/" + image
        img_src = 'http://asosite.alachuasheriff.org/ASOInmateImageHandler.aspx?PicNo=' + inmateid

        #if os.path.isfile(path):
        #print("Image previously saved")
        #uopen = requests.get(img_src, headers=headers)
        #file = open('/home/fladata/Desktop/Python/Mugshots/images/' + image, 'wb')
        #file.write(uopen.content)
        #file.close()
        #else:
        #uopen = requests.get(img_src, headers=headers)
        #file = open('/home/fladata/Desktop/Python/Mugshots/images/' + image, 'wb')
        #file.write(uopen.content)
        #file.close()

        # CHARGES
        chargetables = soup2.select('#GridView1_GridView2_0 > tr')
        chargetables = chargetables[1:]
        counter = 0
        datecheck = datetime.datetime.now() - datetime.datetime.strptime(arrestdate,
        '%Y-%m-%d %H:%M:%S')
        if datecheck.days < 3:
            uopen = requests.get(img_src, headers=headers)
            file = open('/Users/brandon.meyer/Desktop/Python2/Mugshots/images/' + image, 'wb')
            file.write(uopen.content)
            file.close()
            RemDir = '/var/www/html/home/crime/images'

            with sftp.cd(RemDir):
                print(RemDir)
                try:
                    sftp.put('/Users/brandon.meyer/Desktop/Python2/Mugshots/images/' + image)
                except:
                    print('Upload failed')
            print(coun, lastname)
            for testtable in chargetables:
                casenum = testtable.findAll('td')[-5].text
                casenumber = testtable.findAll('td')[-4].text
                agency = testtable.findAll('td')[-3].text
                bondamount = testtable.findAll('td')[-2].text
                chargestatus = testtable.findAll('td')[-1].text

                chargerows = testtable.select('tr')[1:]
                counts = 1

                for charges in chargerows:
                    counter = counter + 1
                    chargenum = charges.select('td')[0].text
                    statute = charges.select('td')[1].text
                    chargename = charges.select('td')[2].text
                    chargenumber = bookingnumber + '-' + str(counter)
                    # print(chargenumber, casenumber, agency, bondamount,
                    #       chargestatus, chargenum, statute, chargename)
                    # print('---')

                    sql = "INSERT INTO `bookings` (name,firstname,middlename,lastname,inmateid,race,sex,age,bookingnumber,arrestdate,image,county, agency) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE name = VALUES(name), firstname = VALUES(firstname), middlename = VALUES(middlename), lastname = VALUES(lastname), inmateid = VALUES(inmateid), race = VALUES(race), sex = VALUES(sex), age = VALUES(age), bookingnumber = VALUES(bookingnumber), arrestdate = VALUES(arrestdate), image = VALUES(image), county=VALUES(county), agency=VALUES(agency)"
                    cur.execute(sql, (name, firstname, middlename, lastname, inmateid,
                    race, sex, age, bookingnumber, arrestdate, image, county, agency))
                    conn.commit()

                    sql2 = "INSERT INTO `charges` (bookingnumber,chargenumber,chargename,agency,statute,casenumber,counts,chargestatus,bondamount) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE bookingnumber = VALUES(bookingnumber), chargenumber = VALUES(chargenumber), chargename = VALUES(chargename), agency = VALUES(agency), statute = VALUES(statute), casenumber = VALUES(casenumber), counts = VALUES(counts), chargestatus = VALUES(chargestatus), bondamount = VALUES(bondamount)"
                    cur.execute(sql2, (bookingnumber, chargenumber, chargename, agency, statute,
                    casenumber, counts, chargestatus, bondamount))
                    conn.commit()
        else:
            continue
