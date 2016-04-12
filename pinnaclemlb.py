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
    
def getData(dates):
    
    r = requests.get("http://www.pinnaclesports.com/webapi/1.15/api/v1/GuestLines/NonLive/3/246").json()
    # League ID 246 (regular season), SportID = 3 (MLB)
    
    events = r['Leagues'][0]['Events']
    game = []
    gameList = []
    for event in events:

        if event['Totals'] and event['PeriodNumber'] == 0 and event['DateAndTime'][:10] == dates[0]:      ### Only get Full Game Line (fix this later!)
            total = float(event['Totals']['Min'])               ### Game Total
            gamedate = event['DateAndTime'][:10]
            gametime = event['DateAndTime'][11:-1]        
            game.append(event['EventId'])                       # Event ID
            game.append(gamedate)                               # Game Date
            game.append(gametime)                               # Game Time
            game.append(event['Totals']['Min'])
            game.append(event['Totals']['OverPrice'])
            game.append(event['Totals']['UnderPrice'])
            
            # print '\neventID:', event['EventId']                        # Game ID
            # print 'date:', gamedate
            # print 'time:', gametime
            # print 'total:', total
            # print 'Over Price:', event['Totals']['OverPrice']    # Over Odds
            # print 'Under Price:', event['Totals']['UnderPrice']  # Under Odds
            
        
            for participants in event['Participants']:
                spread = float(participants['Handicap']['Min'])
                teamTotalOdds = int(participants['TeamTotals']['OverPrice'])
                teamTotal = participants['TeamTotals']['Min']
                if teamTotalOdds == -100:
                    adjTotalOdds = 110
                elif 0 > teamTotalOdds + 10 > -100:          # Adjust by 10 cents for rake
                    adjTotalOdds = 10 + teamTotalOdds - round(teamTotalOdds/100,0)*100
                else:
                    adjTotalOdds = teamTotalOdds + 10
                if adjTotalOdds < 0:
                    decTotalOdds = -(100.0/adjTotalOdds) + 1
                else:
                    decTotalOdds = (adjTotalOdds/100.0) + 1
                # print adjTotalOdds
                # print decTotalOdds
                # print teamTotal
                teamTotal = round((3-decTotalOdds)*teamTotal,3)     # Expected team total 
                game.append(participants['Name'])
                game.append(participants['Pitcher'])
                game.append(participants['MoneyLine'])
                game.append(participants['Handicap']['Min'])
                game.append(participants['Handicap']['Price'])
                game.append(teamTotal)
                # game.append(participants['TeamTotals']['Min'])
                # print 'Team:', participants['Name']                  # Team
                # print 'ML:', participants['MoneyLine']               # Moneyline
                # print 'Spread:', participants['Handicap']['Min']     # Spread
                # print 'Odds:', participants['Handicap']['Price']     # Spread Odds
                # print 'Team Total:', teamTotal                     # Team Total
            if dates[0] == game[1]:
                gameList.append(game)
        game = []
    return gameList


def homeawaySplit(gameList, consensus):
    
    headers = ['HomeAway', 'game_id', 'date', 'time', 'total', 'team', 'pitcher', 'ml', 'spread', 'odds', 'team_total', \
    'opp', 'opp_pitcher', 'opp_ml', 'opp_spread', 'opp_odds', 'opp_total', 'over_price', 'under_price']
    
    aworder = [0,1,2,3,6,7,8,9,10,11,12,13,14,15,16,17,4,5]
    hmorder = [0,1,2,3,12,13,14,15,16,17,6,7,8,9,10,11,4,5]

    holder = []
    gameinfo = []
    teamlist = []
    gameDict = {}

    for game in gameList:
        # print game
        holder = [game[i] for i in hmorder]  # List method to put items into home team order
        holder.insert(0, 'Home')             # Add 'Home' to home teams
        gameinfo.append(holder)
        holder = [game[i] for i in aworder]  # List method to put items into away team order
        holder.insert(0, 'Away')             # Add 'Away' to away teams
        gameinfo.append(holder)
    

    for team in gameinfo:
        for header in headers:
            gameDict[header] = team[headers.index(header)]
        teamlist.append(gameDict)
        gameDict = {}
    
    #### Add consensus % to list
    for team in teamlist:
        if team['team'] not in consensus.keys():
            team['consensus'] = ''
        else:
            team['consensus'] = consensus[team['team']]
    
    return teamlist
    
def consensus():
    
    game = []
    gameList = []
    r = requests.get("http://www.oddsshark.com/mlb/consensus-picks").text

    soup = BeautifulSoup(r)

    data = soup.find('table', {'class': 'consensus-table'})
    
    for rows in data.find_all('tr')[1:-1]:
        if 'class' in rows.attrs.keys() and 'favoured' in rows.attrs['class']:
            game.append('consensus')
        for items in rows.find_all('td'):
            if len(items.text.strip()) > 0:
                game.append(items.text.strip())
    gameList = [game[i:i+8] for i in range(0, len(game), 8)]
    bet_pct = {}
    for game in gameList:
        for items in game:
            if items == 'LAA Los Angeles Angels':       # Fix naming issue between two sites
                game[game.index(items)] = 'LAA LAA Angels'
        if game[0] == 'consensus':
            pct = float(game[1][:-1])/100.0
            bet_pct[game[3].split(' ', 1)[1]] = round(pct,2)
            bet_pct[game[5].split(' ', 1)[1]] = round(1-pct,2)
            # print game[3], pct, game[6], 1-pct
        else:
            pct = float(game[0][:-1])/100.0
            bet_pct[game[2].split(' ', 1)[1]] = round(1-pct,2)
            # print game[2], ":", game[6]
            # print pct
            bet_pct[game[5].split(' ', 1)[1]] = round(pct,2)
            # print game[2], 1-pct, game[6], pct
        # print bet_pct

    return bet_pct
    
    
def linemovement(con, gameinfo, dates):
    # See if there is data in the table - if there is not, they are opening lines
    
    changes = ['total_chg', 'team_total_chg', 'opp_total_chg', 'spread_chg']
    
    with con:

    # bring in past results
        cur = con.cursor()
        cur.execute("SELECT * FROM pinnacle_odds WHERE day_id = %s" % (dates[1]))

        rows = cur.fetchall()
        if len(rows) > 0:
            firstPull = False
        else:
            firstPull = True
    # print firstPull
    # If this is the first run, insert in placeholders and make the opening lines set to the current lines
    if firstPull:
        for game in gameinfo:
            for i in changes:
                game[i] = 0.00
            game['total_open'] = game['total']
            game['team_total_open'] = game['team_total']
            game['opp_total_open'] = game['opp_total']
            game['spread_open'] = game['spread']
            
    # If this isn't the first run, calculate the change and insert into the list
    else:
        holder = []
        pastresults = []
        for row in rows:
            for item in row[1:]:            # All items except primary key ID
                holder.append(item)
            pastresults.append(holder)
            holder = []
        # print "\n\n", pastresults, "\n\n"
                
        for past in pastresults:
            for game in gameinfo:
                if past[5] == game['team'] and past[2] == game['game_id']:
                    print past[5], past[2]
                    game['total_open'] = past[21]
                    game['team_total_open'] = past[22]
                    game['opp_total_open'] = past[23]
                    game['spread_open'] = past[24]
                    game['total_chg'] = float(past[21]) - float(game['total'])
                    game['team_total_chg'] = float(past[22]) - float(game['team_total'])
                    game['opp_total_chg'] = float(past[23]) - float(game['opp_total'])
                    game['spread_chg'] = float(past[24]) - float(game['spread'])
        
    return gameinfo
    
def addtoDb(con, dates, gamelist):

    query = "DELETE FROM pinnacle_odds WHERE day_id = %s" % (dates[1])
    x = con.cursor()
    x.execute(query)

    for i in gamelist:
        with con:
            query = "INSERT INTO pinnacle_odds (day, day_id, game_id, time, home_away, team, pitcher, \
            opp, opp_pitcher, team_total, opp_total, total, ml, spread, \
            odds, consensus, opp_ml, opp_spread, opp_odds, over_price, under_price, \
            total_open, team_total_open, opp_total_open, spread_open, total_chg, team_total_chg, opp_total_chg, spread_chg) \
                    VALUES ("'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'")" % \
                (i['date'], dates[1], i['game_id'], i['time'], i['HomeAway'], i['team'], i['pitcher'], \
                i['opp'], i['opp_pitcher'], i['team_total'], i['opp_total'], i['total'], i['ml'], i['spread'], \
                i['odds'], i['consensus'], i['opp_ml'], i['opp_spread'], i['opp_odds'], i['over_price'], i['under_price'], \
                i['total_open'], i['team_total_open'], i['opp_total_open'], i['spread_open'], i['total_chg'], i['team_total_chg'], i['opp_total_chg'], i['spread_chg'])
            x = con.cursor()
            x.execute(query)
    
    print dates[0], "complete"
    
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
    
    local = False

    if local == False:
        fldr = 'mlb-dfs/'
        serverinfo = security('mysql', fldr)
        con = MySQLdb.connect(host='mysql.server', user=serverinfo[0], passwd=serverinfo[1], db='MurrDogg4$dfs-mlb')

    else:
        fldr = ''
        con = MySQLdb.connect('localhost', 'root', '', 'dfs-mlb')            #### Localhost connection

    today = datetime.date.today()
    dates = datestring(today)
    
    gameList = linemovement(con, homeawaySplit(getData(dates), consensus()), dates)
    addtoDb(con, dates, gameList)
    print gameList


# {'over_price': 114.0, 'opp': u'San Diego Padres', 'opp_ml': 104.0, 'ml': -113.0, 'odds': 151.0, 'HomeAway': 'Away', 'pitcher': u'S. Kazmir', 'opp_spread': 1.5, 'under_price': -126.0, 'consensus': 0.47, 'opp_odds': -164.0, 'opp_pitcher': u'J. Shields', 'spread': -1.5, 'time': u'19:10:00', 'team': u'Los Angeles Dodgers', 'date': u'2016-04-05', 'game_id': 575440282, 'opp_total': 2.905, 'total': 7.5, 'team_total': 3.635}
    
if __name__ == '__main__':
    main()