
CREATE VIEW IF NOT EXISTS v_strategic_rollup AS
SELECT
    o.objective_id,
    o.crucible_id,
    o.objective_title,
    o.objective_status,
    o.objective_target_date,
    o.objective_completed,
    COUNT(DISTINCT p.project_id) AS total_projects,
    COALESCE(SUM(pom.poms_completed), 0) AS total_poms_completed,
    COALESCE(SUM(pom.poms_interrupted), 0) AS total_poms_interrupted,
    ROUND(COALESCE(SUM(pom.poms_completed * pom.pom_mins), 0) / 60.0, 2) AS total_focus_hours,
    CASE
        WHEN o.objective_target_date IS NOT NULL AND o.objective_completed IS NOT NULL
        THEN CAST(ROUND(JULIANDAY(o.objective_completed) - JULIANDAY(o.objective_target_date)) AS INTEGER)
        ELSE NULL
    END AS schedule_variance_days
FROM objectives o
LEFT JOIN projects p ON o.objective_id = p.objective_id
LEFT JOIN pomodoros pom ON p.project_id = pom.project_id
GROUP BY o.objective_id;