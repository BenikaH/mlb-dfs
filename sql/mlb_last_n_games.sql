select * from 
(select day, player_id, playernm_full, team, dk_sal, dkp, (case player_id when @curId then @curRow := @curRow+1 else @curRow := 1 and @curId := player_id end) as rank 
from (select day, 
			player_id, 
			playernm_full, 
			team, 
			dk_sal, 
			dkp 
			from rotoguru where dk_sal <> 0 order by 2,1 desc) a, (select @curRow := 0, @curId := '') r) g where rank <= 5;