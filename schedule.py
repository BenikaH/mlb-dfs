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

def getSchedule(datestr):
    
    print "Starting", datestr
    
    day = datestr[-2:]
    month = datestr[4:6]
    year = datestr[:4]
    
    url = 'http://mlb.mlb.com/gdcross/components/game/mlb/year_'+year+'/month_'+month+'/day_'+day+'/master_scoreboard.json'
    
    r = requests.get(url).json()
    
    games = r['data']['games']['game']
    
    keyList = ['home_file_code', 'home_code', 'home_league_id', 'venue', 'home_division', 'original_date', 'id', \
    'away_division', 'game_data_directory', 'venue_id', 'home_team_name', 'away_team_name', 'game_pk', 'gameday', \
    'away_file_code', 'away_team_id', 'gameday_sw', 'away_name_abbrev', 'location', 'home_ampm', 'tbd_flag', \
    'away_code', 'double_header_sw', 'away_team_city', 'time_date', 'day', 'home_probable_pitcher', 'home_team_city', \
    'game_type', 'time_zone', 'home_team_id', 'home_name_abbrev', 'away_probable_pitcher', 'away_league_id']
    
    gameList = []
    for game in games:          # Get all the game data, then create a dict for each team (home/away)
        ### Home Team
        print game
        if 'home_probable_pitcher' in game.keys():
            gameinfo = {}
            for key in keyList:
                gameinfo[key] = game[key]
            gameinfo['homeaway'] = 'Home'
            gameinfo['team'] = gameinfo['home_name_abbrev']
            gameinfo['opp'] =  gameinfo['away_name_abbrev']
            gameinfo['pitcher'] = gameinfo['home_probable_pitcher']['name_display_roster']
            gameinfo['opp_pitcher'] = gameinfo['away_probable_pitcher']['name_display_roster']
            gameinfo['pitcher_hand'] = gameinfo['home_probable_pitcher']['throwinghand']
            gameinfo['opp_pitcher_hand'] = gameinfo['away_probable_pitcher']['throwinghand']
            gameinfo['pitcher_id'] = gameinfo['home_probable_pitcher']['id']
            gameinfo['opp_pitcher_id'] = gameinfo['away_probable_pitcher']['id']
            gameList.append(gameinfo)
            ### Away Team
            gameinfo = {}
            for key in keyList:
                gameinfo[key] = game[key]
            gameinfo['homeaway'] = 'Away'
            gameinfo['team'] = gameinfo['away_name_abbrev']
            gameinfo['opp'] =  gameinfo['home_name_abbrev']
            gameinfo['pitcher'] = gameinfo['away_probable_pitcher']['name_display_roster']
            gameinfo['opp_pitcher'] = gameinfo['home_probable_pitcher']['name_display_roster']
            gameinfo['pitcher_hand'] = gameinfo['away_probable_pitcher']['throwinghand']
            gameinfo['opp_pitcher_hand'] = gameinfo['home_probable_pitcher']['throwinghand']
            gameinfo['pitcher_id'] = gameinfo['away_probable_pitcher']['id']
            gameinfo['opp_pitcher_id'] = gameinfo['home_probable_pitcher']['id']
            gameList.append(gameinfo)
    
    return gameList

def addtoDb(con, gameList, datestr):
    
    query = "DELETE FROM schedule WHERE day_id = %s" % (datestr)
    x = con.cursor()
    x.execute(query)

    with con:
        for i in gameList:
            query = "INSERT INTO schedule (day_id, homeaway, team, opp, pitcher, opp_pitcher, pitcher_hand, \
                    opp_pitcher_hand, pitcher_id, opp_pitcher_id, venue, venue_id, game_id, game_data_directory, \
                    gameday, time_date, home_team_id, away_team_id, location, game_pk, double_header_sw, \
                    game_type, weekday) \
                    VALUES ("'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'")" % \
                (datestr, i['homeaway'], i['team'], i['opp'], i['pitcher'], i['opp_pitcher'], i['pitcher_hand'], \
                i['opp_pitcher_hand'], i['pitcher_id'], i['opp_pitcher_id'], i['venue'], i['venue_id'], i['id'], i['game_data_directory'], \
                i['gameday'], i['time_date'], i['home_team_id'], i['away_team_id'], i['location'], i['game_pk'], i['double_header_sw'], 
                i['game_type'], i['day'])

            x = con.cursor()
            x.execute(query)
    
    return
    
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
    
    
    gameday = datetime.date.today()
    datestr = datestring(gameday)[1]
    gameList = getSchedule(datestr)
    
    addtoDb(con, gameList, datestr)
        
    return
    
if __name__ == '__main__':
    main()