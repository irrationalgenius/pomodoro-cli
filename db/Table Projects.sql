
DROP TABLE IF EXISTS projects CASCADE;
CREATE TABLE projects (
    project_id         SERIAL PRIMARY KEY,
    project_code       TEXT NOT NULL UNIQUE,
    objective_id       INT REFERENCES objectives(objective_id) ON DELETE SET NULL,
    project_name       TEXT NOT NULL,
    project_priority   TEXT NOT NULL DEFAULT 'SCHEDULE'
                       CHECK (project_priority IN ('DO', 'SCHEDULE', 'DELEGATE', 'DELETE')),
    project_status     TEXT NOT NULL DEFAULT 'ACTIVE'
                       CHECK (project_status IN ('ACTIVE', 'PAUSED', 'COMPLETED')),
    weekly_pom_budget  INTEGER NOT NULL DEFAULT 0,
    project_contacts   TEXT,
    project_created    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_updated    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_objective ON projects(objective_id);
CREATE INDEX idx_projects_status    ON projects(project_status);
CREATE INDEX idx_projects_priority  ON projects(project_priority);

CREATE OR REPLACE FUNCTION trg_projects_updated_func()
RETURNS TRIGGER AS $$
BEGIN
    NEW.project_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_projects_updated
BEFORE UPDATE ON projects
FOR EACH ROW
EXECUTE FUNCTION trg_projects_updated_func();