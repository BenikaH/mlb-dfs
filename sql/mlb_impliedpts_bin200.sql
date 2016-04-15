-- Change 200 to different value to change bin size
set @binsize = 200;

select
c.position,
c.dk_sal,
b.avg_pts

from

(select
position,
dk_sal_bin,
sum(sum_dkp)/sum(player_count) as avg_pts
from
(select
position,
round(dk_sal/@binsize,0)*@binsize as dk_sal_bin,
dk_sal,
sum_dkp,
player_count
from v_implied_pts) a group by 1,2) b
inner join (
select
position,
-- Change 200 to different value to change bin size
round(dk_sal/@binsize,0)*@binsize as dk_sal_bin,
dk_sal,
sum_dkp,
player_count
from v_implied_pts) c
on b.dk_sal_bin = c.dk_sal_bin and b.position = c.position