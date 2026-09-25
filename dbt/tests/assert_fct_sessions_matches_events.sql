-- The incremental table must agree with a from-scratch aggregation of all
-- loaded events: catches stale sessions, e.g. one crossing midnight into a
-- newly loaded month that the lookback failed to recompute.
select f.user_session
from {{ ref('fct_sessions') }} f
full outer join {{ ref('int_sessions') }} i
    on f.user_session = i.user_session
where f.user_session is null
   or i.user_session is null
   or f.events != i.events
   or f.purchases != i.purchases
   or f.session_end != i.session_end
