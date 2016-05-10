select
sc.pitcher_id,
pmap.mlb_name,
sc.team,
sc.opp,
sc.pitcher_hand,
dk.dk_sal,
imp.imp_pts,
sc.venue,
sc.time_date,
pt.ip as 'IP 3Y',
ps.ip as 'IP CY',
pt.SIERA as 'SIERA 3Y',
ps.SIERA as 'SIERA CY',
pt.FIP as 'FIP 3Y',
ps.FIP as 'FIP CY',
pt.k9 as 'K/9 3Y',
ps.k9 as 'K/9 CY',
ths.wOBA as 'opp wOBA',
ths.iso as 'opp ISO',
ths.k_pct as 'opp K%',
(ths.k_pct / 20.4 * pt.k9) as 'adj K/9 3Y',
(ths.k_pct / 20.4 * ps.k9) as 'adj K/9 CY',
odds.ml,
odds.total,
odds.opp_total,
odds.opp_total_chg,
dk.dk_sal as 'day0',
sal.day1,
sal.day2,
sal.day3,
sal.day14,
sal.day30,
dk.dk_sal - sal.day1 as '1 Day Chg'
dk.dk_sal - sal.day2 as '2 Day Chg',
dk.dk_sal - sal.day3 as '3 Day Chg',
dk.dk_sal - sal.day7 as '1 Week Chg',
dk.dk_sal - sal.day14 as '2 Week Chg',
dk.dk_sal - sal.day30 as '30 Day Chg'

from
(select pid, pcode, s as dk_sal from draftkings_playerlist where day_id = '@today' and ContestStartTimeSuffix = '@slate' and pp = 1) dk

left join player_map pmap on dk.pcode = pmap.nfbc_id
left join schedule sc on pmap.mlb_id = sc.pitcher_id and sc.day_id = '@today'
left join pitchers_total pt on pmap.fg_id = pt.player_id
left join pitchers_season ps on pmap.fg_id = ps.player_id and ps.season = '2016'
left join team_map opptmap on sc.opp = opptmap.Abbr
left join ( select
			case when vsArm = 'L' then 'LHP' when vsArm = 'R' then 'RHP' else 'NA' end as vsArm,
			season,
			team,
			pa,
			wOBA,
			iso,
			k_pct
			from
			v_teamhitting_season where season = '2016') ths on opptmap.Nickname = ths.team and sc.pitcher_hand = ths.vsArm
left join team_map tmap on sc.team = tmap.Abbr
left join pinnacle_odds odds on tmap.PinnacleName = odds.team and odds.day_id = '@today'
left join dksal_history sal on sal.player_id = pmap.mlb_id
left join v_implied_pts imp on dk.dk_sal = imp.dk_sal and position = 'Pitcher'

order by odds.ml asc, dk.dk_sal desc;