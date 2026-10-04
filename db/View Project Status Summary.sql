
CREATE VIEW IF NOT EXISTS v_project_status_summary AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,
    p.project_priority,
    p.project_status,
    p.weekly_pom_budget,
    COALESCE(SUM(pom.poms_completed), 0) AS total_poms_completed,
    COALESCE(SUM(pom.poms_interrupted), 0) AS total_poms_interrupted,
    ROUND(COALESCE(SUM(pom.poms_completed * pom.pom_mins), 0) / 60.0, 2) AS total_focus_hours,
    MIN(pom.pomo_created) AS first_session_date,
    MAX(pom.pomo_created) AS last_session_date
FROM projects p
LEFT JOIN pomodoros pom ON p.project_id = pom.project_id
GROUP BY p.project_id;