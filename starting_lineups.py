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

def getlineups(url):
    
    r = requests.get(url).text
    soup = BeautifulSoup(r)

    weather = soup.find_all("div", {"class" : "dlineups-topboxcenter"})
    
    gamelist = []
    for rows in weather:            # Get weather information for each game and split into time, weather, direction
        game = rows.text
        game = game.replace('\r','').replace('\n','')
        game1 = game.split('\t')
        game2 = []
        for games in game1:
            game = games.strip()
            if game != '':
                game2.append(game)
        gamelist.append(game2)

    for games in gamelist:          # Add rain and dome info based on weather
        if len(games) != 3:
            if 'rain' in games[1]:
                games.append('Rain')
            else:
                games.append('Dome')

    hold = []
    for i in gamelist:              # Duplicate each entry to account for home/away teams -- used to 
        hold.append(i)              # combine all info into individual player entries later
        hold.append(i)
    gamelist = hold


    teams = soup.find_all("div", {"class" : ["dlineups-mainbar-away", "dlineups-mainbar-home"]})
    teamlist = []
    for team in teams:              # Get team names
        team1 = team.text
        teamlist.append(team1)

    teamsplit = []                  # Split teams out into sets of 2 (this may not be necessary)
    size = 2
    teamsplit = [teamlist[i:i+size] for i  in range(0, len(teamlist), size)]


    lineups = soup.find_all("div", {"class" : ["dlineups-vplayer", "dlineups-hplayer", "dlineups-empty"]})

    missing = 0                     # variable to count number of missing lineups
    lineuplist = []                 # Get players in starting lineup
    for player in lineups:
        if 'Lineup' in player.text: # If pending, append a blank entry, otherwise append player name and ID
            missing += 1
            for i in range(9):
                lineuplist.append(['',''])
        else:
            newplayer = player.find_all("a")
            for i in newplayer:
                temp1 = []
                temp1.append(i.text)
                plink = i['href']
                temp1.append(plink[plink.find('=')+1:]) # Appends the player ID from rotowire
                lineuplist.append(temp1)

    lineuplist = [lineuplist[i:i+9] for i in range(0, len(lineuplist), 9)]  # Split into groups of 9


    combo = []
    for i in teamlist:
        for players in lineuplist[teamlist.index(i)]:   # Insert team name for each player entry
            if '@' in i:
                players.insert(0,i[2:])
            else:
                players.insert(0,i)
            players.append(lineuplist[teamlist.index(i)].index(players)+1)  # Insert spot in order
            for weather in gamelist[teamlist.index(i)]:
                players.append(weather)                 # Insert the weather information
            combo.append(players)
    # print combo

    headers = ['Team', 'PlayerNm', 'PlayerID', 'BattingOrder', 'Time', 'Weather', 'WindDir']

    playerList = []

    for players in combo:       # Add data into a list of dictionaries
        playerdict = {}
        for header in headers:
            playerdict[header] = players[headers.index(header)]
        playerList.append(playerdict)
    
    return playerList

    
def addtoDb(con, playerList, datestr):
    
    query = "DELETE FROM starting_lineups WHERE day_id = %s" % (datestr)
    x = con.cursor()
    x.execute(query)

    with con:
        for i in playerList:
            query = "INSERT INTO starting_lineups (day_id, player_id, playernm, team, bat_order, game_start, weather, wind_dir) \
                    VALUES ("'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'")" % \
                (datestr, i['PlayerID'], i['PlayerNm'], i['Team'], i['BattingOrder'], i['Time'], i['Weather'], i['WindDir'])

            x = con.cursor()
            x.execute(query)
    
    return
    
def main():
    
    local = False

    if local == False:
        fldr = 'mlb-dfs/'
        serverinfo = security('mysql', fldr)
        con = MySQLdb.connect(host='mysql.server', user=serverinfo[0], passwd=serverinfo[1], db='MurrDogg4$dfs-mlb')

    else:
        fldr = ''
        con = MySQLdb.connect('localhost', 'root', '', 'dfs-mlb')            #### Localhost connection
    
    gameday = datetime.date.today()
    datestr = datestring(gameday)[1]
        
    url = 'http://www.rotowire.com/baseball/daily_lineups.htm'
    
    playerList = getlineups(url)
    print playerList
    addtoDb(con, playerList, datestr)
    
    return

if __name__ == '__main__':
    main()