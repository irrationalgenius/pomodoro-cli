
DROP TABLE IF EXISTS evidences CASCADE;
CREATE TABLE evidences (
    evidence_id SERIAL PRIMARY KEY,
    evidence_title TEXT NOT NULL,
    evidence_text  TEXT,
    evidence_location  TEXT,
    evidence_file   BYTEA
);

CREATE TABLE objective_evidences(
    evidence_id INT REFERENCES evidences(evidence_id) ON DELETE NO ACTION,
    objective_id INT REFERENCES objectives(objective_id) ON DELETE NO ACTION
);

CREATE TABLE project_evidences(
    evidence_id INT REFERENCES evidences(evidence_id) ON DELETE NO ACTION,
    project_id INT REFERENCES projects(project_id) ON DELETE NO ACTION
);

CREATE TABLE pomodoro_evidences(
    evidence_id INT REFERENCES evidences(evidence_id) ON DELETE NO ACTION,
    pomodoro_id INT REFERENCES pomodoros(pomo_id) ON DELETE NO ACTION
);