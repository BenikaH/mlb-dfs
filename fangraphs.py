#!/usr/local/bin/python2.7

from bs4 import BeautifulSoup
import requests
import csv
import datetime
import MySQLdb
import time


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

def getteamdata(url, headers):
    
    results = []
    teamDict = {}
    teamList = []
    
    if 'vsArm' in headers:
        arm = True
        if url[url.find('month')+6:url.find('month')+8] == '13':
            vsArm = 'L'
        else:
            vsArm = 'R'
    else:
        arm = False
        vsArm = ''
    
    r = requests.get(url).text
    soup = BeautifulSoup(r)
    
    data = soup.find('table', {'class': 'rgMasterTable'})
    
    teamData = data.find_all('tr', {'class': ['rgRow', 'rgAltRow']})
    
    for team in teamData:
        cols = team.find_all('td', {'class': ['grid_line_regular', 'grid_line_break']})
        for col in cols[1:]:
            results.append(col.text.replace(' %', ''))              # append all results to temp list and remove % sign
            
        ## check if this is a L/R split, if it is, append and then check to see if it is a seasonal breakout or total
        ## if it is not a L/R split and is not a seasonal breakout, append a '0' for season
        if arm == True:
            if len(results) + 2 == len(headers):
                results.insert(0, '0')                              # Season = 0 for total
                results.insert(0, vsArm)                            # Append L/R split arm
            else:
                results.insert(0, vsArm)
        else:
            if len(results) < len(headers):
                results.insert(0, '0')
        for header in headers:
            teamDict[header] = results[headers.index(header)]
        teamList.append(teamDict)                                   # append individual dicts to teamList
        results = []
        teamDict = {}
        
    return teamList
    
        
def getplayerdata(url, headers):
    
    results = []
    playerDict = {}
    playerList = []
    
    if 'vsArm' in headers:
        arm = True
        ssn_col = 3
        if url[url.find('month')+6:url.find('month')+8] == '13':
            vsArm = 'L'
        elif url[url.find('month')+6:url.find('month')+8] == '14':
            vsArm = 'R'
        else:
            vsArm = 'A'
    else:
        arm = False
        ssn_col = 2
        vsArm = ''
    
    r = requests.get(url).text
    soup = BeautifulSoup(r)
    
    data = soup.find('table', {'class': 'rgMasterTable'})
    
    playerData = data.find_all('tr', {'class': ['rgRow', 'rgAltRow']})
    
    for player in playerData:
        links = player.find('a')   # Add player ID
        plLink = links['href']
        idpos = plLink.find('id=')+3
        pospos = plLink.find('&position')
        plid = plLink[idpos:pospos]
        position = plLink[pospos+10:]
        
        if arm == True:
            results.append(vsArm)
        results.append(plid)
        results.append(position)
        cols = player.find_all('td', {'class': ['grid_line_regular', 'grid_line_break']})
        for col in cols[1:]:
            results.append(col.text.replace(' %', ''))              # append all results to temp list and remove % sign
        if len(results) < len(headers):
            results.insert(ssn_col, '0')
        for header in headers:
            playerDict[header] = results[headers.index(header)]
        playerList.append(playerDict)                                   # append individual dicts to teamList
        results = []
        playerDict = {}
    
    return playerList
    
def addtoDb(con, data, tblname, tbltype, year):
    
    if tbltype in [5,6,7,8]:
        query = "DELETE FROM %s" % (tblname)
    else:
        query = "DELETE FROM %s WHERE season = %s" % (tblname, year)
    x = con.cursor()
    x.execute(query)

    for i in data:
        with con:
            if tbltype == 1 or tbltype == 7:
                query = "INSERT INTO %s (season, team, pa, bb_pct, k_pct, bbk_ratio, avg, \
                                        obp, slg, ops, iso, spd, babip, ubr, \
                                        wGDP, wSB, wRC, wRAA, wOBA, wRCplus) \
                        VALUES ("'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                                "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                                "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'")" % \
                    (tblname,\
                    i['season'], i['team'], i['pa'], i['bb_pct'], i['k_pct'], i['bbk_ratio'], i['avg'], \
                    i['obp'], i['slg'], i['ops'], i['iso'], i['spd'], i['babip'], i['ubr'], \
                    i['wGDP'], i['wSB'], i['wRC'], i['wRAA'], i['wOBA'], i['wRCplus'])
            elif tbltype == 2 or tbltype == 8:
                query = "INSERT INTO %s (vsArm, season, team, pa, bb_pct, k_pct, bbk_ratio, \
                                        sb, avg, obp, slg, ops, iso, spd, \
                                        babip, wRC, wRAA, wOBA, wRCplus) \
                        VALUES ("'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                                "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                                "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'")" % \
                    (tblname,\
                    i['vsArm'], i['season'], i['team'], i['pa'], i['bb_pct'], i['k_pct'], i['bbk_ratio'], \
                    i['sb'], i['avg'], i['obp'], i['slg'], i['ops'], i['iso'], i['spd'], \
                    i['babip'], i['wRC'], i['wRAA'], i['wOBA'], i['wRCplus'])
            elif tbltype == 3 or tbltype == 5:
                query = "INSERT INTO %s (vsArm, player_id, pos, season, playernm_full, team, pa, \
                                        bb_pct, k_pct, bbk_ratio, sb, avg, obp, slg, \
                                        ops, iso, spd, babip, wRC, wRAA, wOBA, \
                                        wRCplus, gbfb_ratio, hrfb_ratio) \
                        VALUES ("'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                                "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                                "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                                "'"%s"'", "'"%s"'", "'"%s"'")" % \
                    (tblname,\
                    i['vsArm'], i['player_id'], i['pos'], i['season'], i['playernm_full'], i['team'], i['pa'], \
                    i['bb_pct'], i['k_pct'], i['bbk_ratio'], i['sb'], i['avg'], i['obp'], i['slg'], \
                    i['ops'], i['iso'], i['spd'], i['babip'], i['wRC'], i['wRAA'], i['wOBA'], \
                    i['wRCplus'], i['gbfb_ratio'], i['hrfb_ratio'])
            elif tbltype == 4 or tbltype == 6:
                query = "INSERT INTO %s (player_id, pos, season, playernm_full, team, g, gs, \
                                        ip, k9, bb9, kbb_ratio, hr_per9, k_pct, bb_pct, \
                                        k_minus_bb_pct, avg, whip, babip, lob_pct, ERAminus, FIPminus, \
                                        xFIPminus, ERA, FIP, ERA_minus_FIP, xFIP, SIERA) \
                        VALUES ("'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                                "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                                "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", \
                                "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'", "'"%s"'")" % \
                    (tblname,\
                    i['player_id'], i['pos'], i['season'], i['playernm_full'], i['team'], i['g'], i['gs'], \
                    i['ip'], i['k9'], i['bb9'], i['kbb_ratio'], i['hr_per9'], i['k_pct'], i['bb_pct'], \
                    i['k_minus_bb_pct'], i['avg'], i['whip'], i['babip'], i['lob_pct'], i['ERAminus'], i['FIPminus'], \
                    i['xFIPminus'], i['ERA'], i['FIP'], i['ERA_minus_FIP'], i['xFIP'], i['SIERA'])
                    
            else:
                return
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
    
    yearFst = 2014
    yearLst = 2016
    
    teamheader1 = ['season','team', 'pa', 'bb_pct', 'k_pct', 'bbk_ratio', 'avg', 'obp', 'slg', 'ops', 'iso', 'spd', 'babip', \
                'ubr', 'wGDP', 'wSB', 'wRC', 'wRAA', 'wOBA', 'wRCplus']
    
    teamheader2 = ['vsArm', 'season', 'team', 'pa', 'bb_pct', 'k_pct', 'bbk_ratio', 'sb', 'avg', 'obp', 'slg', 'ops', 'iso', 'spd', 'babip', \
                'wRC', 'wRAA', 'wOBA', 'wRCplus']
    
    hitterheader1 = ['vsArm', 'player_id', 'pos', 'season', 'playernm_full', 'team', 'pa', 'bb_pct', 'k_pct', 'bbk_ratio', 'sb', 'avg', \
                    'obp', 'slg', 'ops', 'iso', 'spd', 'babip', 'wRC', 'wRAA', 'wOBA', 'wRCplus', 'gbfb_ratio', 'hrfb_ratio']
       
    pitcherheader1 = ['player_id', 'pos', 'season', 'playernm_full', 'team', 'g', 'gs', 'ip', 'k9', 'bb9', 'kbb_ratio', 'hr_per9', \
                    'k_pct', 'bb_pct', 'k_minus_bb_pct', 'avg', 'whip', 'babip', 'lob_pct', 'ERAminus', 'FIPminus', 'xFIPminus', \
                    'ERA', 'FIP', 'ERA_minus_FIP', 'xFIP', 'SIERA']
    
    pitcherStatUrls = ['http://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=0&type=c%2c7%2c8%2c13%2c36%2c37%2c38%2c40%2c-1%2c120%2c121%2c217%2c-1%2c41%2c42%2c43%2c44%2c-1%2c117%2c118%2c119%2c-1%2c6%2c45%2c124%2c-1%2c62%2c122&season='+str(yearLst)+'&month=0&season1='+str(yearFst)+'&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_5000', \
    'http://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=0&type=c%2c7%2c8%2c13%2c36%2c37%2c38%2c40%2c-1%2c120%2c121%2c217%2c-1%2c41%2c42%2c43%2c44%2c-1%2c117%2c118%2c119%2c-1%2c6%2c45%2c124%2c-1%2c62%2c122&season='+str(yearLst)+'&month=0&season1='+str(yearLst)+'&ind=0&team=0&rost=0&age=0&filter=&players=0&sort=21%2ca&page=1_5000']
    
    teamUrlName = ['TeamHitting_Total', 'TeamHitting_Total_vL', 'TeamHitting_Total_vR',\
                    'TeamHitting_Season', 'TeamHitting_Season_vL', 'TeamHitting_Season_vR',\
                    'TeamHitting_Last14']
    
    teamUrlDict = {
        'TeamHitting_Total': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=1&season='+str(yearLst)+'&month=0&season1='+str(yearFst)+'&ind=0&team=0%2cts&rost=0&age=0&filter=&players=0&sort=19%2cd&page=1_5000',
            'headers': 1,
            'database': 7,
            'tblname': 'teamhitting_total'
        },
        'TeamHitting_Season': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=1&season='+str(yearLst)+'&month=0&season1='+str(yearFst)+'&ind=1&team=0%2cts&rost=0&age=0&filter=&players=0&sort=19%2cd&page=1_5000',
            'headers': 1,
            'database': 7,
            'tblname': 'teamhitting_season'
        },
        'TeamHitting_Total_vL': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=c,6,34,35,36,21,23,37,38,39,40,53,41,52,51,50,54&season='+str(yearLst)+'&month=13&season1='+str(yearFst)+'&ind=0&team=0,ts&rost=0&age=0&filter=&players=0',
            'headers': 2,
            'database': 8,
            'tblname': 'teamhitting_total_vL'
        },
        'TeamHitting_Total_vR': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=c,6,34,35,36,21,23,37,38,39,40,53,41,52,51,50,54&season='+str(yearLst)+'&month=14&season1='+str(yearFst)+'&ind=0&team=0,ts&rost=0&age=0&filter=&players=0',
            'headers': 2,
            'database': 8,
            'tblname': 'teamhitting_total_vR'
        },
        'TeamHitting_Season_vL': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=c,6,34,35,36,21,23,37,38,39,40,53,41,52,51,50,54&season='+str(yearLst)+'&month=13&season1='+str(yearLst)+'&ind=1&team=0,ts&rost=0&age=0&filter=&players=0',
            'headers': 2,
            'database': 2,
            'tblname': 'teamhitting_season_vL'
        },
        'TeamHitting_Season_vR': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=c,6,34,35,36,21,23,37,38,39,40,53,41,52,51,50,54&season='+str(yearLst)+'&month=14&season1='+str(yearLst)+'&ind=1&team=0,ts&rost=0&age=0&filter=&players=0',
            'headers': 2,
            'database': 2,
            'tblname': 'teamhitting_season_vR'
        },
        'TeamHitting_Last14': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=1&season='+str(yearLst)+'&month=2&season1='+str(yearFst)+'&ind=0&team=0%2cts&rost=0&age=0&filter=&players=0',
            'headers': 1,
            'database': 7,
            'tblname': 'teamhitting_last14'
        }
    }

    hitterUrlName = ['hitters_season_vL', 'hitters_season_vR', 'hitters_total_vL', 'hitters_total_vR', \
                    'hitters_last14', 'hitters_last7']
    
    hitterUrlDict = {
        'hitters_season_vL': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=c,6,34,35,36,21,23,37,38,39,40,53,41,52,51,50,54,42,47&season='+str(yearLst)+'&month=13&season1='+str(yearLst)+'&ind=1&team=0&rost=0&age=0&filter=&players=0&page=1_5000',
            'headers': 3,
            'database': 3,
            'tblname': 'hitters_season_vL'
        },
        'hitters_season_vR': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=c,6,34,35,36,21,23,37,38,39,40,53,41,52,51,50,54,42,47&season='+str(yearLst)+'&month=14&season1='+str(yearLst)+'&ind=1&team=0&rost=0&age=0&filter=&players=0&page=1_5000',
            'headers': 3,
            'database': 3,
            'tblname': 'hitters_season_vR'
        },
        'hitters_total_vL': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=c,6,34,35,36,21,23,37,38,39,40,53,41,52,51,50,54,42,47&season='+str(yearLst)+'&month=13&season1='+str(yearFst)+'&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_5000',
            'headers': 3,
            'database': 5,
            'tblname': 'hitters_total_vL'
        },
        'hitters_total_vR': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=c,6,34,35,36,21,23,37,38,39,40,53,41,52,51,50,54,42,47&season='+str(yearLst)+'&month=14&season1='+str(yearFst)+'&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_5000',
            'headers': 3,
            'database': 5,
            'tblname': 'hitters_total_vR'
        },
        'hitters_last14': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=c,6,34,35,36,21,23,37,38,39,40,53,41,52,51,50,54,42,47&season='+str(yearLst)+'&month=2&season1='+str(yearLst)+'&ind=1&team=0&rost=0&age=0&filter=&players=0&page=1_5000',
            'headers': 3,
            'database': 5,
            'tblname': 'hitters_last14'
        },
        'hitters_last7': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=bat&lg=all&qual=0&type=c,6,34,35,36,21,23,37,38,39,40,53,41,52,51,50,54,42,47&season='+str(yearLst)+'&month=1&season1='+str(yearLst)+'&ind=1&team=0&rost=0&age=0&filter=&players=0&page=1_5000',
            'headers': 3,
            'database': 5,
            'tblname': 'hitters_last7'
        }
    }
    
    pitcherUrlName = ['pitchers_season', 'pitchers_total']
    
    pitcherUrlDict = {
        'pitchers_season': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=0&type=c,7,8,13,36,37,38,40,-1,120,121,217,-1,41,42,43,44,-1,117,118,119,-1,6,45,124,-1,62,122&season='+str(yearLst)+'&month=0&season1='+str(yearLst)+'&ind=1&team=0&rost=0&age=0&filter=&players=0&page=1_5000',
            'headers': 4,
            'database': 4,
            'tblname': 'pitchers_season'
        },
        'pitchers_total': {
            'url': 'http://www.fangraphs.com/leaders.aspx?pos=all&stats=pit&lg=all&qual=0&type=c,7,8,13,36,37,38,40,-1,120,121,217,-1,41,42,43,44,-1,117,118,119,-1,6,45,124,-1,62,122&season='+str(yearLst)+'&month=0&season1='+str(yearFst)+'&ind=0&team=0&rost=0&age=0&filter=&players=0&page=1_5000',
            'headers': 4,
            'database': 6,
            'tblname': 'pitchers_total'
        }
    }
    
    for urls in teamUrlName:
        if teamUrlDict[urls]['headers'] == 1:
            headers = teamheader1
        else:
            headers = teamheader2
        tblname = teamUrlDict[urls]['tblname']
        database = teamUrlDict[urls]['database']
        print urls, "\n"
        data = getteamdata(teamUrlDict[urls]['url'], headers)
        addtoDb(con, data, tblname, database, yearLst)
        time.sleep(1)

    for urls in hitterUrlName:
        headers = hitterheader1
        tblname = hitterUrlDict[urls]['tblname']
        database = hitterUrlDict[urls]['database']
        print urls, "\n"
        data = getplayerdata(hitterUrlDict[urls]['url'], headers)
        # print data
        addtoDb(con, data, tblname, database, yearLst)
        time.sleep(1)
        
    for urls in pitcherUrlName:
        headers = pitcherheader1
        tblname = pitcherUrlDict[urls]['tblname']
        database = pitcherUrlDict[urls]['database']
        print urls, "\n"
        data = getplayerdata(pitcherUrlDict[urls]['url'], headers)
        # print data
        addtoDb(con, data, tblname, database, yearLst)
        time.sleep(1)
        
    
if __name__ == '__main__':
    main()