
DROP VIEW pomos_active;
CREATE VIEW pomos_active AS
WITH ac AS(SELECT COALESCE(pomo_id_parent, pomo_id) AS root_id
           FROM pomodoros
           GROUP BY COALESCE(pomo_id_parent, pomo_id)
           HAVING MAX(pomo_complete) = 0)
SELECT p.pomo_id,
       p.pomo_id_parent,
       COALESCE(p.pomo_id_parent, p.pomo_id) AS grouping_id,
       p.pomo_created,
       p.priority,
       p.pomo_name,
       p.pomo_complete,
       p.notes
FROM pomodoros p
  INNER JOIN ac ON COALESCE(p.pomo_id_parent, p.pomo_id) = ac.root_id
ORDER BY grouping_id,
         CASE
           WHEN p.pomo_id_parent IS NULL THEN 0
           ELSE 1
         END,
         p.pomo_created ASC, priority;