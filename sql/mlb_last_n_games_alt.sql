select * from (
select a.day, a.player_id, a.playernm_full, a.team, a.dk_sal, @id_rank := IF(@cur_player = player_id, @id_rank + 1, 1) as id_rank
, @cur_player := player_id 
from (
select * from rotoguru order by player_id, day desc) a) b where id_rank <= 5;