#!/usr/local/bin/python2.7

import requests
import MySQLdb
import csv
from bs4 import BeautifulSoup
import datetime

# >>> SECONDS = '/Date(1416458650000)/'.split('(')[1][:-5]
# >>> SECONDS
# '1416458650'
# >>> print datetime.datetime.fromtimestamp(float(SECONDS)).strftime('%Y-%m-%d %H:%M:%S')
# 2014-11-19 23:44:10
# >>> secs = '/Date(1460415900000)/'.split('(')[1][:-5]
# >>> secs
# '1460415900'
# >>> print datetime.datetime.fromtimestamp(float(secs)).strftime('%Y-%m-%d %H:%M:%S')
# 2016-04-11 19:05:00
# >>> tstamp = datetime.datetime.fromtimestamp(float(secs)).strftime('%Y-%m-%d %H:%M:%S')
# >>> tstamp
# '2016-04-11 19:05:00'


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

def slateinfo(url):
    
    ### 1) pull in slates 2) split by day, 3) identify main slate, 
    
    slateList = {}
    
    r = requests.get(url).json()
    # Get Days
    dayList = []
    for slates in r['DraftGroups']:
        if slates['StartDate'][:10] not in dayList:
            dayList.append(slates['StartDate'][:10])
    
    for day in dayList:
        slateList[day] = {}
        for slates in r['DraftGroups']:
            if slates['StartDate'][:10] == day:
                slateList[day][slates['DraftGroupId']] = slates
                if not slateList[day][slates['DraftGroupId']]['ContestStartTimeSuffix']:
                    slateList[day][slates['DraftGroupId']]['ContestStartTimeSuffix'] = 'Main'
                else:
                    slateList[day][slates['DraftGroupId']]['ContestStartTimeSuffix'] = slateList[day][slates['DraftGroupId']]['ContestStartTimeSuffix'].strip()
    return slateList

def playerdata(slate):
    
    slateurl = 'https://www.draftkings.com/lineup/getavailableplayers?draftGroupId=' + str(slate)
    print slateurl
    
    r = requests.get(slateurl).json()
    if 'playerList' not in r.keys():
        return
    else:
        playerdata = r['playerList']
    
    return playerdata

def addtoDb(con, players, slate, datestr):
    
    print slate['DraftGroupId']
    
    query = "DELETE FROM draftkings_playerlist WHERE DraftGroupId = %s" % (slate['DraftGroupId'])
    x = con.cursor()
    x.execute(query)

    with con:
        for i in players:
            query = "INSERT INTO draftkings_playerlist (day, day_id, DraftGroupId, ContestTypeId, StartDate, GameCount, ContestStartTimeSuffix, \
                                    ContestStartTimeType, pid, pcode, tsid, fn, ln, fnu, \
                                    lnu, pn, dgst, tid, htid, atid, htabbr, \
                                    atabbr, posid, slo, IsDisabledFromDrafting, s, ppg, orr, \
                                    opn, pp, i, news) \
                    VALUES ("'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'")" % \
                (datestr[0], datestr[1], slate['DraftGroupId'], slate['ContestTypeId'], slate['StartDateEst'], slate['GameCount'], slate['ContestStartTimeSuffix'], \
                slate['ContestStartTimeType'], i['pid'], i['pcode'], i['tsid'], i['fn'], i['ln'], i['fnu'], \
                i['lnu'], i['pn'], i['dgst'], i['tid'], i['htid'], i['atid'], i['htabbr'], \
                i['atabbr'], i['posid'], i['slo'], i['IsDisabledFromDrafting'], i['s'], i['ppg'], i['or'], \
                i['opn'], i['pp'], i['i'], i['news'])

            x = con.cursor()
            x.execute(query)
    
    
    return

def main():
    
    local = True

    if local == False:
        fldr = 'mlb-dfs/'
        serverinfo = security('mysql', fldr)
        con = MySQLdb.connect(host='mysql.server', user=serverinfo[0], passwd=serverinfo[1], db='MurrDogg4$dfs-mlb')

    else:
        fldr = ''
        con = MySQLdb.connect('localhost', 'root', '', 'dfs-mlb')            #### Localhost connection
    
    url = "https://www.draftkings.com/lobby/getcontests?sport=MLB"
    
    slateList = slateinfo(url)
    
    for day in slateList.keys():
        dates = [day, day.replace('-','')]
        print "Starting: ", day
        for slateid in slateList[day].keys():
            slate = slateList[day][slateid]
            players = playerdata(slateid)
            addtoDb(con, players, slate, dates)
    
    return
    
if __name__ == '__main__':
    main()