insert into dksal_history (player_id, playernm_full, day1, day2, day3, day4, day5, day6, day7, day8, day9, day10, day11, day12, day13, day14, day15, day16, day17, day18, day19, day20, day21, day22, day23, day24, day25, day26, day27, day28, day29, day30)
(select
player_id,
playernm_full,
sum(day1) as day1,
sum(day2) as day2,
sum(day3) as day3,
sum(day4) as day4,
sum(day5) as day5,
sum(day6) as day6,
sum(day7) as day7,
sum(day8) as day8,
sum(day9) as day9,
sum(day10) as day10,
sum(day11) as day11,
sum(day12) as day12,
sum(day13) as day13,
sum(day14) as day14,
sum(day15) as day15,
sum(day16) as day16,
sum(day17) as day17,
sum(day18) as day18,
sum(day19) as day19,
sum(day20) as day20,
sum(day21) as day21,
sum(day22) as day22,
sum(day23) as day23,
sum(day24) as day24,
sum(day25) as day25,
sum(day26) as day26,
sum(day27) as day27,
sum(day28) as day28,
sum(day29) as day29,
sum(day30) as day30
from
(select
player_id,
playernm_full,
case when rank = 1 then dk_sal end as day1,
case when rank = 2 then dk_sal end as day2,
case when rank = 3 then dk_sal end as day3,
case when rank = 4 then dk_sal end as day4,
case when rank = 5 then dk_sal end as day5,
case when rank = 6 then dk_sal end as day6,
case when rank = 7 then dk_sal end as day7,
case when rank = 8 then dk_sal end as day8,
case when rank = 9 then dk_sal end as day9,
case when rank = 10 then dk_sal end as day10,
case when rank = 11 then dk_sal end as day11,
case when rank = 12 then dk_sal end as day12,
case when rank = 13 then dk_sal end as day13,
case when rank = 14 then dk_sal end as day14,
case when rank = 15 then dk_sal end as day15,
case when rank = 16 then dk_sal end as day16,
case when rank = 17 then dk_sal end as day17,
case when rank = 18 then dk_sal end as day18,
case when rank = 19 then dk_sal end as day19,
case when rank = 20 then dk_sal end as day20,
case when rank = 21 then dk_sal end as day21,
case when rank = 22 then dk_sal end as day22,
case when rank = 23 then dk_sal end as day23,
case when rank = 24 then dk_sal end as day24,
case when rank = 25 then dk_sal end as day25,
case when rank = 26 then dk_sal end as day26,
case when rank = 27 then dk_sal end as day27,
case when rank = 28 then dk_sal end as day28,
case when rank = 29 then dk_sal end as day29,
case when rank = 30 then dk_sal end as day30
from (
select * from (select day, player_id, playernm_full, dk_sal, dkp, (case player_id when @curId then @curRow := @curRow+1 else @curRow := 1 and @curId := player_id end) as rank from (select day, player_id, playernm_full, team, dk_sal, dkp from rotoguru where dk_sal <> 0 order by 2,1 desc) a, (select @curRow := 0, @curId := '') r) g where rank <= 30) tbl) tbl2 group by 1,2);