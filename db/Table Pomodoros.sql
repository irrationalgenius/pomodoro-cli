
DROP TABLE IF EXISTS pomodoros CASCADE;
CREATE TABLE pomodoros (
    pomo_id              SERIAL PRIMARY KEY,
    pomo_id_parent       INT REFERENCES pomodoros(pomo_id) ON DELETE CASCADE,
    project_id           INT REFERENCES projects(project_id) ON DELETE CASCADE,
    priority             INTEGER DEFAULT 4,
    pomo_created         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    pomo_name            TEXT,
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
    pomo_updated         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    poms_achieved        INTEGER NOT NULL DEFAULT 0,
    pomo_complete        INTEGER NOT NULL DEFAULT 0
                         CHECK (pomo_complete IN (0, 1)),
    notes                TEXT,

    CONSTRAINT chk_anchor_name CHECK (
        pomo_id_parent IS NOT NULL OR pomo_name IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_pomodoros_parent   ON pomodoros(pomo_id_parent);
CREATE INDEX IF NOT EXISTS idx_pomodoros_project  ON pomodoros(project_id);
CREATE INDEX IF NOT EXISTS idx_pomodoros_created  ON pomodoros(pomo_created);
CREATE INDEX IF NOT EXISTS idx_pomodoros_friction ON pomodoros(pomo_friction);
CREATE INDEX IF NOT EXISTS idx_pomodoros_complete ON pomodoros(pomo_complete);

CREATE OR REPLACE FUNCTION trg_pomodoros_updated_func()
RETURNS TRIGGER AS $$
BEGIN
    NEW.pomo_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_pomodoros_updated
BEFORE UPDATE ON pomodoros
FOR EACH ROW
EXECUTE FUNCTION trg_pomodoros_updated_func();