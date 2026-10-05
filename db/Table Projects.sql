

CREATE TABLE projects (
    project_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_code       TEXT NOT NULL UNIQUE, -- e.g., 'NET-10G', 'CLI-APP'
    objective_id       INTEGER REFERENCES objectives(objective_id) ON DELETE SET NULL,
    project_name       TEXT NOT NULL,
    project_priority   TEXT NOT NULL DEFAULT 'SCHEDULE'
                       CHECK (project_priority IN ('DO', 'SCHEDULE', 'DELEGATE', 'DELETE')),
    project_status     TEXT NOT NULL DEFAULT 'ACTIVE'
                       CHECK (project_status IN ('ACTIVE', 'PAUSED', 'COMPLETED')),
    weekly_pom_budget  INTEGER NOT NULL DEFAULT 0,
    project_contacts   TEXT,
    project_created    TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    project_updated    TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX idx_projects_objective ON projects(objective_id);
CREATE INDEX idx_projects_status    ON projects(project_status);
CREATE INDEX idx_projects_priority  ON projects(project_priority);

CREATE TRIGGER trg_projects_updated
AFTER UPDATE ON projects
FOR EACH ROW
BEGIN
    UPDATE projects
    SET project_updated = datetime('now', 'localtime')
    WHERE project_id = OLD.project_id;
END;

CREATE TRIGGER trg_projects_lifecycle
BEFORE UPDATE OF project_status ON projects
FOR EACH ROW
BEGIN
    UPDATE projects
    SET
        project_updated = datetime('now', 'localtime')
    WHERE project_id = NEW.project_id;
END;