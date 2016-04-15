#!/usr/local/bin/python2.7

from bs4 import BeautifulSoup
import requests
import datetime
import MySQLdb
import time


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


def getplayerdata(url):
    r = requests.get(url).text
    soup = BeautifulSoup(r)

    data = soup.find("td", {"colspan": 9})
    if data is None:
        return
    else:

        playerdata = data.find_all("p")

        for items in playerdata:
            players = items.text

        data = players[1:].split("\n")[:-1]

        if len(data) > 1:
            headers = data[0].split(";")


            players = []
            for item in data[1:]:
                player = item.split(";")
                players.append(player)

            playerlist = []
            for player in players:
                playerdict = {}
                for header in headers:
                    playerdict[header] = player[headers.index(header)].strip()
                playerlist.append(playerdict)

            for player in playerlist:
                player['playernm_first'] = player['Name'].split(', ')[1]
                player['playernm_last'] = player['Name'].split(', ')[0]
        else:
            print 'no games'
            return

        playerdict = {}

        for player in playerlist:
            playerdict[player['MLB_ID']] = player

        time.sleep(1)

        return playerdict

def combinesites(dkdata, fddata):

    missingids = []
    dkheaders = dkdata[dkdata.keys()[0]].keys()
    fdheaders = fddata[fddata.keys()[0]].keys()

    missingheaders = []
    for header in fdheaders:
        if header not in dkheaders:
            missingheaders.append(header)

    comboheaders = dkheaders
    for header in fdheaders:
        if header not in dkheaders:
            comboheaders.append(header)

    for player in dkdata.keys():
        if player in fddata.keys():
            for header in missingheaders:
                dkdata[player][header] = fddata[player][header]

    for id in fddata.keys():
        if id not in dkdata.keys():
            missingids.append(id)

    if len(missingids) > 0:
        for id in missingids:
            dkdata[id] = fddata[id]

    for player in dkdata.keys():
        for header in comboheaders:
            if header not in dkdata[player].keys():
                dkdata[player][header] = ''

    return dkdata

def addtoDb(con, players, data, datestr):

    query = "DELETE FROM rotoguru WHERE day = %s" % (datestr)
    x = con.cursor()
    x.execute(query)

    with con:
        for i in players:
            query = "INSERT INTO rotoguru (day, player_id, playernm_full, playernm_first, playernm_last, team, opp, \
                                    fd_pos, dk_pos, starter_ind, bat_order, fdp, dkp, fd_sal, \
                                    dk_sal, dblhdr_ind, game_id, team_runs, opp_runs) \
                    VALUES ("'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'")" % \
                (data[i]['Date'], data[i]['MLB_ID'], data[i]['Name'], data[i]['playernm_first'], data[i]['playernm_last'], data[i]['Team'], data[i]['Oppt'], \
                data[i]['FD posn'], data[i]['DK posn'], data[i]['Starter'], data[i]['Bat order'], data[i]['FD pts'], data[i]['DK pts'], data[i]['FD sal'], \
                data[i]['DK sal'], data[i]['dblhdr'], data[i]['GID'], data[i]['Tm Runs'], data[i]['Opp Runs'])

            x = con.cursor()
            x.execute(query)

    return

def datestring(month, day, year):

    if month < 10:
        monthstr = '0' + str(month)
    else:
        monthstr = str(month)

    if day < 10:
        daystr = '0' + str(day)
    else:
        daystr = str(day)

    datestr = str(year) + monthstr + daystr

    return datestr

def main():

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

    # month = 4
    # day = 29
    # year = 2015

    myfile = fldr + 'daterun.txt'
    with open(myfile) as f:
        g = f.read().splitlines()
        for date in g:
            datestr = date

    # for day in range(1,31):
    #     datestr = datestring(month, day, year)
            print datestr, "Started"
            day = datestr[-2:]
            month = datestr[4:6]
            year = datestr[:4]

            dkurl = 'http://rotoguru1.com/cgi-bin/byday.pl?game=dk&month='+str(month)+'&day='+str(day)+'&year='+str(year)+'&scsv=1'
            fdurl = 'http://rotoguru1.com/cgi-bin/byday.pl?game=fd&month='+str(month)+'&day='+str(day)+'&year='+str(year)+'&scsv=1'

            dkdata = getplayerdata(dkurl)

            if dkdata is not None:

                fddata = getplayerdata(fdurl)
                playerdata = combinesites(dkdata, fddata)
                players = playerdata.keys()
                print playerdata[players[1]]

                addtoDb(con, players, playerdata, datestr)
                print datestr, "Complete"
                time.sleep(1)

            else:
                print datestr, "Does Not Exist"
                time.sleep(1)

    return

if __name__ == '__main__':
    main()
