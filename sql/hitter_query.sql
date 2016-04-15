select
pmap.mlb_name,
dk.pn,
pmap.mlb_team,
sc.opp,
sc.homeaway,
sc.venue,
dk.dk_sal,
lu.bat_order,
pmap.bats,
sc.opp_pitcher_hand,
ht.pa as 'PA 3Y',
hs.pa as 'PA CY',
l14.pa as 'PA L14',
l7.pa as 'PA L7',
ht.wOBA as 'wOBA 3Y',
ht.wOBA - hto.wOBA as 'wOBA 3Y diff',
hs.wOBA as 'wOBA CY',
hs.wOBA - hso.wOBA as 'wOBA CY diff',
l14.wOBA as 'wOBA L14',
l7.wOBA as 'wOBA L7',
ht.iso as 'ISO 3Y',
ht.iso - hto.iso as 'ISO 3Y diff',
hs.iso as 'ISO CY',
hs.iso - hso.iso as 'ISO CY diff',
l14.iso as 'ISO L14',
l7.iso as 'ISO L7',
ht.hrfb_ratio as 'HR/FB 3Y',
hs.hrfb_ratio as 'HR/FB CY',
odds.ml,
odds.total,
odds.team_total,
odds.team_total_chg,
lut.weather,
lut.wind_dir,
sal.day1,
sal.day2,
sal.day3,
sal.day14,
sal.day30,
dk.dk_sal - sal.day1 as '1 Day Chg',
dk.dk_sal - sal.day2 as '2 Day Chg',
dk.dk_sal - sal.day3 as '3 Day Chg',
dk.dk_sal - sal.day7 as '1 Week Chg',
dk.dk_sal - sal.day14 as '2 Week Chg',
dk.dk_sal - sal.day30 as '30 Day Chg'
from
(select
pn,
pcode,
pid,
s as dk_sal
from draftkings_playerlist where day_id = '@today' and pn not in ('SP', 'RP') and ContestStartTimeSuffix = '@slate') dk
left join player_map pmap on dk.pcode = pmap.nfbc_id
left join starting_lineups lu on pmap.rotowire_id = lu.player_id and lu.day_id = '@today'
left join dksal_history sal on sal.player_id = pmap.mlb_id
left join schedule sc on pmap.mlb_team = sc.team and sc.day_id = '@today'
left join team_map tmap on sc.team = tmap.Abbr
left join (select distinct team, weather, wind_dir from starting_lineups where day_id = '@today') lut on tmap.RotowireName = lut.team
left join hitters_last14 l14 on pmap.fg_id = l14.player_id
left join hitters_last14 l7 on pmap.fg_id = l7.player_id
left join pinnacle_odds odds on tmap.PinnacleName = odds.team and odds.day_id = '@today'
left join ( select
			player_id,
			case when vsArm = 'L' then 'LHP' when vsArm = 'R' then 'RHP' else 'NA' end as vsArm,
			pa,
			wOBA,
			iso,
			hrfb_ratio,
			ops,
			spd
			from v_hitters_total) ht on pmap.fg_id = ht.player_id and sc.opp_pitcher_hand = ht.vsArm
left join ( select
			player_id,
			case when vsArm = 'L' then 'RHP' when vsArm = 'R' then 'LHP' else 'NA' end as vsArm,
			pa,
			wOBA,
			iso,
			hrfb_ratio,
			ops,
			spd
			from v_hitters_total) hto on pmap.fg_id = hto.player_id and sc.opp_pitcher_hand = hto.vsArm
left join ( select
			player_id,
			case when vsArm = 'L' then 'LHP' when vsArm = 'R' then 'RHP' else 'NA' end as vsArm,
			pa,
			wOBA,
			iso,
			hrfb_ratio,
			ops,
			spd
			from v_hitters_season where season = '2016') hs on pmap.fg_id = hs.player_id and sc.opp_pitcher_hand = hs.vsArm
left join ( select
			player_id,
			case when vsArm = 'L' then 'RHP' when vsArm = 'R' then 'LHP' else 'NA' end as vsArm,
			pa,
			wOBA,
			iso,
			hrfb_ratio,
			ops,
			spd
			from v_hitters_season where season = '2016') hso on pmap.fg_id = hso.player_id and sc.opp_pitcher_hand = hso.vsArm;