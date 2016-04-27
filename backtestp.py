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


    with con:
        x = con.cursor()
        x.execute(query)
        columns = x.description


        rows = x.fetchall()

#        fp = open('csv_outputs/'+title+'.csv', 'w')
#        myFile = csv.writer(fp)
#        myFile.writerows(rows)
#        fp.close()

    return rows

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
            if len(newlist) > 3:
                siteDict[newlist[0]]['server'] = newlist[3]

    if site == 'mysql':
        info = [siteDict[site]['username'],siteDict[site]['password'], siteDict[site]['server']]
    else:
        info = [siteDict[site]['username'],siteDict[site]['password']]

    return info

def getRanks(pitcherlist, weights):
    pitcherlist[:] = [d for d in pitcherlist if d.get('Player') != None]

    ## reverse = True indicates 'lower the better'
    ## Salary
    newlist = sorted(pitcherlist, key=lambda k: k['Salary'], reverse=True)
    for lst in newlist:
        lst['SalaryRank'] = newlist.index(lst)+1
    ## SIERA 3Y
    newlist = sorted(newlist, key=lambda k: k['SIERA_3Y'], reverse=True)
    for lst in newlist:
        lst['SIERA_3YRank'] = newlist.index(lst)+1
    ## SIERA CY
    newlist = sorted(newlist, key=lambda k: k['SIERA_CY'], reverse=True)
    for lst in newlist:
        lst['SIERA_CYRank'] = newlist.index(lst)+1
    ## K/9 3Y
    newlist = sorted(newlist, key=lambda k: k['K9_3Y'])
    for lst in newlist:
        lst['K9_3YRank'] = newlist.index(lst)+1
    ## Adj. K/9 CY
    newlist = sorted(newlist, key=lambda k: k['adj_K9_CY'])
    for lst in newlist:
        lst['adj_K9_CYRank'] = newlist.index(lst)+1
    ## Opp wOBA
    newlist = sorted(newlist, key=lambda k: k['opp_wOBA'], reverse=True)
    for lst in newlist:
        lst['opp_wOBARank'] = newlist.index(lst)+1
    ## Vegas ML
    newlist = sorted(newlist, key=lambda k: k['Vegas_ML'], reverse=True)
    for lst in newlist:
        lst['Vegas_MLRank'] = newlist.index(lst)+1
    ## Opp Team Total
    newlist = sorted(newlist, key=lambda k: k['Opp_Total'], reverse=True)
    for lst in newlist:
        lst['Opp_TotalRank'] = newlist.index(lst)+1

    for lst in newlist:
        pts = 0.0
        for key in weights.keys():
            pts += weights[key] * float(lst[key])
        lst['TotalRankPts'] = pts

    newlist = sorted(newlist, key=lambda k: k['TotalRankPts'], reverse=True)
    for lst in newlist:
        lst['TotalRank'] = newlist.index(lst)+1

    return newlist


def main():

    today = datetime.date.today()
    dates = datestring(today)

    headers = ['PlayerID','Player','Team','Matchup','Throws','Salary','Venue','DateTime',\
    'IP_3Y','IP_CY','SIERA_3Y','SIERA_CY','FIP_3Y','FIP_CY','K9_3Y','K9_CY',\
    'opp_wOBA','opp_ISO','Opp_Krt','adj_K9_3Y','adj_K9_CY','Vegas_ML','OU','Opp_Total','Opp_Total_Chg']

    weights = {'SalaryRank': 0.5, 'SIERA_3YRank': 1.0, 'SIERA_CYRank': 1.4, 'K9_3YRank': 0.5, 'adj_K9_CYRank': 1.9, \
                'opp_wOBARank': 1.9, 'Vegas_MLRank': 2.1, 'Opp_TotalRank': 0.7}

    localfile = 'local.txt'
    with open(localfile) as f:
        g = f.read()
    if g == 'True':
        local = True
    else:
        local = False

    daylist = ['20160412','20160413','20160414','20160415','20160416','20160417','20160418','20160419','20160420','20160421','20160422','20160423','20160424','20160425','20160426']
    daylist = ['20160424','20160425','20160426']



    if local == False:
        fldr = 'mlb-dfs/'
        serverinfo = security('mysql', fldr)
        con = MySQLdb.connect(host=serverinfo[2], user=serverinfo[0], passwd=serverinfo[1], db='MurrDogg4$dfs-mlb')

    else:
        fldr = ''
        con = MySQLdb.connect('localhost', 'root', '', 'dfs-mlb')            #### Localhost connection


    playerscore = []
    for day_id in daylist:
        masterlist = []
        plList = opensql('pitcherback.sql', fldr, con, day_id)

        for pl in plList:
            plDict = {}
            for header in headers:
                plDict[header] = pl[headers.index(header)]
            masterlist.append(plDict)

        rankedlist = getRanks(masterlist, weights)

        for player in rankedlist:
            playerscore.append([day_id, player['PlayerID'], player['Player'], round(player['TotalRankPts'], 2), player['TotalRank']])

    for player in playerscore:
        print player

    return

if __name__ == '__main__':
    main()
