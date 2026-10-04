
CREATE TABLE evidences (
    evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_title TEXT NOT NULL,
    evidence_text  TEXT,
    evidence_ref   TEXT
);

CREATE TABLE objective_evidences(
    evidence_id REFERENCES evidences(evidence_id) ON DELETE NO ACTION ,
    project_id   REFERENCES projects(project_id) ON DELETE NO ACTION
);

CREATE TABLE project_evidences(
    evidence_id REFERENCES evidences(evidence_id) ON DELETE NO ACTION ,
    project_id REFERENCES projects(project_id) ON DELETE NO ACTION
);

CREATE TABLE pomodoro_evidences(
    evidence_id REFERENCES evidences(evidence_id) ON DELETE NO ACTION ,
    pomodoro_id REFERENCES pomodoros(pomo_id) ON DELETE NO ACTION
);