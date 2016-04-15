#!/usr/local/bin/python2.7

import requests
import MySQLdb
import csv
from bs4 import BeautifulSoup
import datetime

def datestring(dt):

    year = dt.year
    month = dt.month
    day = dt.day

    if day < 10:
        day = '0' + str(day)
    else:
        day = str(day)

    if month < 10:
        month = '0' + str(month)
    else:
        month = str(month)

    datestr = str(year) + '-' + month + '-' + day
    dayid = str(year) + month + day

    dates = [datestr, dayid]

    return dates

def opensql(filenm, fldr, con, day_id):
    
    sqlfile = fldr + 'sql/' + filenm

    with open(sqlfile) as f:
    
        g = f.read()

        query = g.replace('\n',' ').replace('@today', day_id)
        print query

    with con:
        x = con.cursor()
        x.execute(query)
        columns = x.description
        print columns

        rows = x.fetchall()

        for row in rows:
            print 'row', row
    
    return

def security(site,fldr):
    
    info = []
    myfile = fldr + 'myinfo.txt'

    siteDict = {}
    with open(myfile) as f:
        g = f.read().splitlines()
        for row in g:
            newlist = row.split(' ')
            siteDict[newlist[0]] = {}
            siteDict[newlist[0]]['username'] = newlist[1]
            siteDict[newlist[0]]['password'] = newlist[2]
                
    info = [siteDict[site]['username'],siteDict[site]['password']]
    
    return info

def main():
    
    today = datetime.date.today()
    dates = datestring(today)
    
    localfile = 'local.txt'
    with open(localfile) as f:
        g = f.read()
        
    if g == 'True':
        local = True
    else:
        local = False

    if local == False:
        fldr = 'mlb-dfs/'
        serverinfo = security('mysql', fldr)
        con = MySQLdb.connect(host='mysql.server', user=serverinfo[0], passwd=serverinfo[1], db='MurrDogg4$dfs-mlb')

    else:
        fldr = ''
        con = MySQLdb.connect('localhost', 'root', '', 'dfs-mlb')            #### Localhost connection
    
    day_id = dates[1]
    opensql('pitching_query.sql', fldr, con, day_id)

    return

if __name__ == '__main__':
    main()
