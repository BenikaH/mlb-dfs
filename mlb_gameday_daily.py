#!/usr/local/bin/python2.7

from bs4 import BeautifulSoup
import re
import requests
import csv
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



def getdailydata(datestr):
    
    
    print "Starting", datestr
    
    day = datestr[-2:]
    month = datestr[4:6]
    year = datestr[:4]

    htmltext = requests.get("http://gd2.mlb.com/components/game/mlb/year_"+year+"/month_"+month+"/day_"+day+"/master_scoreboard.json").json()
    # toplevel = json.load(htmltext)
    # games = toplevel["data"]["games"]["game"]
    games = htmltext["data"]["games"]["game"]
    
    # Go through game info and pull directory list of games -- these links provide the data    
    gamedirList = []
    if isinstance(games, dict):
        gamedirList.append(games["game_data_directory"])
    else:
        for game in games:
            gamedirList.append(game["game_data_directory"])
    
    return gamedirList

def getgamedata(game, datestr):
    
    defaultkeys = ['day', 'id', 'name', 'name_display_first_last', 'pos', 'ab', 'r', \
                    'h', 'bb', 'so', 'hr', 'rbi', 'avg', 'sac', \
                    'ao', 'go', 'sb', 'cs', 'lob', 'hbp', 'po', \
                    'bo', 'd', 'a', 'e', 't', 'sf', 'gidp', \
                    '2b', '3b', 'fdp', 'dkp', 'fldg', 's_r', 's_h', \
                    's_bb', 's_so', 's_hr', 's_rbi', 'note', 'hp_umpnm', 'hp_umpid', \
                    '1b_umpnm', '1b_umpid', '2b_umpnm', '2b_umpid', '3b_umpnm', '3b_umpid', 'venuenm', \
                    'venue_id', 'weather', 'wind']

# Open boxscore json file in directory
    url = "http://gd2.mlb.com" + game + "/boxscore.json"
    print url
    try:
        htmltext = requests.get(url)
    except:
        return
    boxscore = htmltext.json()
    boxdata = boxscore["data"]["boxscore"]
    gameinfo = boxdata["game_info"]
    batting = boxdata["batting"]
    venue = getvenue(boxdata)
    weather = getweather(gameinfo)
    umpires = getumpires(gameinfo)
    playerList = []
    for i in range(0,2):        # Home and Away
        batters = boxdata["batting"][i]["batter"]
        textdata = boxdata["batting"][i]["text_data"]
        for batter in batters:
            batter["2b"] = 0
            batter["3b"] = 0
        # Append double data
        doubles = hitTypes('doubles',textdata)
        if not doubles:
            doubles = []
        for players in doubles:
            for batter in batters:
                if batter["name"] == players[0]:
                    batter["2b"] = players[1]
        # Append triple data
        triples = hitTypes('triples',textdata)
        if not triples:
            triples = []
        for players in triples:
            for batter in batters:
                if batter["name"] == players[0]:
                    batter["3b"] = players[1]                    
        for batter in batters:
            batter["day"] = datestr    # Add Date Info
            
            ##### Add Venue Info
            batter["venue_id"] = venue[0]
            batter["venuenm"] = venue[1]
            ##### End Venue
            
            ##### Add Weather Info
            batter["weather"] = weather[0]
            batter["wind"] = weather[1]
            ##### End Weather
            
            ##### Add Umpire Info
            batter["hp_umpid"] = umpires["HP"][0]
            batter["hp_umpnm"] = umpires["HP"][1]
            batter["1b_umpid"] = umpires["1B"][0]
            batter["1b_umpnm"] = umpires["1B"][1]
            batter["2b_umpid"] = umpires["2B"][0]
            batter["2b_umpnm"] = umpires["2B"][1]
            batter["3b_umpid"] = umpires["3B"][0]
            batter["3b_umpnm"] = umpires["3B"][1]
            ##### End Umpire Info
            
            fdp = (int(batter["h"]) + int(batter["2b"]) + int(batter["3b"]) * 2 + int(batter["hr"]) * 3 \
             + int(batter["r"]) + int(batter["rbi"]) + int(batter["bb"]) + int(batter["hbp"]) \
             + int(batter["sb"]) * 2) - ((int(batter["ab"]) - int(batter["h"])) * 0.25)
            dkp = (int(batter["h"]) * 3 + int(batter["2b"]) * 2 + int(batter["3b"]) * 5 + int(batter["hr"]) * 7 \
             + int(batter["r"]) * 2 + int(batter["rbi"]) * 2 + int(batter["bb"]) * 2 + int(batter["hbp"]) * 2 \
             + int(batter["sb"]) * 5) - (int(batter["cs"]) * 2)
            batter["fdp"] = fdp  
            batter["dkp"] = dkp
            
            for key in defaultkeys:
                if key not in batter.keys():
                    batter[key] = ''
            playerList.append(batter)
            
    # print len(playerList)
    
    return playerList

# Function to scrape the text data from the boxscore for info like doubles, triples, etc.
def hitTypes(hittype, text):    
    reg = re.search('<'+hittype+'>(.*?)</'+hittype+'>', text)
    if reg:
        newtext = reg.group()
        newtext = newtext.replace('</'+hittype+'>','')
        newtext = newtext.replace('<'+hittype+'>','')
        newtext = newtext.split('), ')
        hits = []
        players = []
        for i in newtext:
            char = i.index('(')
            i = i[:char-1]
            if re.search('\d', i):
                plNm = i[:-2]
                num = i[-1:]
                players.append(plNm)
                players.append(num)
            else:
                players.append(i)
            hits.append(players)
            players = []
        
        for i in hits:
            if len(i) < 2:
                i.append(u'1')
    
        return hits
            
def getumpires(gameinfo):
    
    regex = r'<umpire (.*?)>'   # Umpires are in a set of umpire tags
    
    umpires = re.findall(regex,gameinfo)

    regex1 = r'id="(.*?)"'      # Each umpire tag has id, name, position
    regex2 = r'name="(.*?)"'
    regex3 = r'position="(.*?)"'

    umpholder = []
    temp = []
    umpPos = []

    for ump in umpires:         # Get id, name, pos for each ump and add it to a list of umpire info
        info1 = re.findall(regex1, ump)[0]
        info2 = re.findall(regex2, ump)[0]
        info3 = re.findall(regex3, ump)[0]
        temp.append(info1)
        temp.append(info2)
        temp.append(info3)
        umpPos.append(info3)
        umpholder.append(temp)
        temp = []

    umpList = []

    umpDict = {}
    for pos in umpPos:  # Creates dict of umpires for each game based on Pos -- {'1B' : [ID,Nm], '2B' : [ID,Nm]}
        for ump in umpholder:
            if ump[2] == pos:
                umpDict[pos] = [ump[0],ump[1]]
    return umpDict    

def getvenue(boxscore):
    venue = [boxscore["venue_id"], boxscore["venue_name"]]
    return venue

def getweather(gameinfo):
    weather = []
    regex = r'<weather>(.*?)</weather>'
    weather.append(re.findall(regex,gameinfo)[0])
    regex = r'<wind>(.*?)</wind>'
    weather.append(re.findall(regex,gameinfo)[0])
    return weather
    

def addtoDb(con, gamedata, datestr):

    query = "DELETE FROM mlbgamedata WHERE day = %s" % (datestr)
    x = con.cursor()
    x.execute(query)

    with con:
        for i in gamedata:
            query = "INSERT INTO mlbgamedata (day, player_id, playernm_abbr, playernm_full, pos, ab, r, \
                                    h, bb, so, hr, rbi, avg, sac, \
                                    ao, go, sb, cs, lob, hbp, po, \
                                    bo, d, a, e, t, sf, gidp, \
                                    2b, 3b, fdp, dkp, fldg, s_r, s_h, \
                                    s_bb, s_so, s_hr, s_rbi, note, hp_umpnm, hp_umpid, \
                                    1b_umpnm, 1b_umpid, 2b_umpnm, 2b_umpid, 3b_umpnm, 3b_umpid, venuenm, \
                                    venue_id, weather, wind) \
                    VALUES ("'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                            "'"%s"'", "'"%s"'", "'"%s"'")" % \
                (i['day'], i['id'], i['name'], i['name_display_first_last'], i['pos'], i['ab'], i['r'], \
                i['h'], i['bb'], i['so'], i['hr'], i['rbi'], i['avg'], i['sac'], \
                i['ao'], i['go'], i['sb'], i['cs'], i['lob'], i['hbp'], i['po'], \
                i['bo'], i['d'], i['a'], i['e'], i['t'], i['sf'], i['gidp'], \
                i['2b'], i['3b'], i['fdp'], i['dkp'], i['fldg'], i['s_r'], i['s_h'], \
                i['s_bb'], i['s_so'], i['s_hr'], i['s_rbi'], i['note'], i['hp_umpnm'], i['hp_umpid'], \
                i['1b_umpnm'], i['1b_umpid'], i['2b_umpnm'], i['2b_umpid'], i['3b_umpnm'], i['3b_umpid'], i['venuenm'], \
                i['venue_id'], i['weather'], i['wind'])

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
        
    datestr = '20150531'
    games = getdailydata(datestr)           # List
    # print games
    for game in games:
        gamedata = getgamedata(game, datestr)
        addtoDb(con, gamedata, datestr)
    
    return
    
if __name__ == '__main__':
    main()