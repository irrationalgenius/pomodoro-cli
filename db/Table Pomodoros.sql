

CREATE TABLE pomodoros (
    pomo_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pomo_id_parent   INTEGER REFERENCES pomodoros(pomo_id) ON DELETE CASCADE,
    project_id       INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    pomo_created     TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    pomo_name        TEXT, -- NULL permitted for continuation rows
    poms_planned     INTEGER NOT NULL DEFAULT 1,
    poms_completed   INTEGER NOT NULL DEFAULT 0,
    poms_interrupted INTEGER NOT NULL DEFAULT 0,
    pom_mins         INTEGER NOT NULL DEFAULT 25,
    pomo_updated     TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    notes            TEXT,
    pomo_complete    INTEGER NOT NULL DEFAULT 0
                     CHECK (pomo_complete IN (0, 1)),

    -- Enforce naming: Must have a name IF it is an anchor row
    CONSTRAINT chk_anchor_name CHECK (
        pomo_id_parent IS NOT NULL OR pomo_name IS NOT NULL
    )
);

CREATE INDEX idx_pomodoros_parent  ON pomodoros(pomo_id_parent);
CREATE INDEX idx_pomodoros_project ON pomodoros(project_id);
CREATE INDEX idx_pomodoros_created ON pomodoros(pomo_created);

CREATE TRIGGER trg_pomodoros_updated
AFTER UPDATE ON pomodoros
FOR EACH ROW
BEGIN
    UPDATE pomodoros
    SET pomo_updated = datetime('now', 'localtime')
    WHERE pomo_id = OLD.pomo_id;
END;