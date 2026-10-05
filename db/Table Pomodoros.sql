
DROP TABLE pomodoros;
CREATE TABLE pomodoros (
    pomo_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pomo_id_parent       INTEGER REFERENCES pomodoros(pomo_id) ON DELETE CASCADE,
    project_id           INTEGER REFERENCES projects(project_id) ON DELETE CASCADE,
    pomo_created         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    pomo_name            TEXT, -- Permitted NULL on continuation rows
    poms_planned         INTEGER NOT NULL DEFAULT 1,
    poms_interrupted     INTEGER NOT NULL DEFAULT 0,
    pom_mins             INTEGER NOT NULL DEFAULT 25,
    pomo_effort          INTEGER NOT NULL DEFAULT 3 
                         CHECK (pomo_effort BETWEEN 1 AND 5),
    pomo_energy          TEXT NOT NULL DEFAULT 'NORMAL' 
                         CHECK (pomo_energy IN ('LOW', 'NORMAL', 'PEAK')),
    pomo_interrupt_type  TEXT NOT NULL DEFAULT 'NONE' 
                         CHECK (pomo_interrupt_type IN ('NONE', 'INTERNAL', 'EXTERNAL')),
    pomo_friction        TEXT NOT NULL DEFAULT 'FLOW' 
                         CHECK (pomo_friction IN ('FLOW', 'TOOLING', 'AMBIGUOUS', 'DEPENDENCY')),
    pomo_updated         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    pomo_complete        INTEGER NOT NULL DEFAULT 0 
                         CHECK (pomo_complete IN (0, 1)),
    notes                TEXT, -- Standardized micro-AAR format: [Friction | Fix/Artifact]

    -- Enforce naming rule: must have a name unless linked to an anchor parent
    CONSTRAINT chk_anchor_name CHECK (
        pomo_id_parent IS NOT NULL OR pomo_name IS NOT NULL
    )
);

-- Operational Performance Indexes
CREATE INDEX IF NOT EXISTS idx_pomodoros_parent   ON pomodoros(pomo_id_parent);
CREATE INDEX IF NOT EXISTS idx_pomodoros_project  ON pomodoros(project_id);
CREATE INDEX IF NOT EXISTS idx_pomodoros_created  ON pomodoros(pomo_created);
CREATE INDEX IF NOT EXISTS idx_pomodoros_friction ON pomodoros(pomo_friction);
CREATE INDEX IF NOT EXISTS idx_pomodoros_complete ON pomodoros(pomo_complete);


CREATE TRIGGER IF NOT EXISTS trg_pomodoros_updated
AFTER UPDATE ON pomodoros
FOR EACH ROW
BEGIN
    UPDATE pomodoros 
    SET pomo_updated = datetime('now', 'localtime') 
    WHERE pomo_id = OLD.pomo_id;
END;
