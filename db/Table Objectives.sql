
-- The Operations Layer
CREATE TABLE objectives (
    objective_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    crucible_id            INTEGER UNIQUE REFERENCES crucibles(crucible_id) ON DELETE SET NULL,
    objective_title        TEXT NOT NULL,
    objective_description  TEXT,
    objective_target_date  TEXT, -- ISO-8601:YYYY-MM-DD HH:MM:SS
    objective_status       TEXT NOT NULL DEFAULT 'ACTIVE'
                           CHECK (objective_status IN ('ACTIVE', 'COMPLETED', 'ON_HOLD', 'ARCHIVED')),
    objective_created      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    objective_updated      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    objective_completed    TEXT  -- Populated when objective_status -> 'COMPLETED'
);

CREATE INDEX idx_objectives_status ON objectives(objective_status);
CREATE INDEX idx_objectives_target ON objectives(objective_target_date);

CREATE TRIGGER trg_objectives_lifecycle
BEFORE UPDATE OF objective_status ON objectives
FOR EACH ROW
BEGIN
    UPDATE objectives
    SET
        objective_updated = datetime('now', 'localtime'),
        objective_completed = CASE
            WHEN NEW.objective_status = 'COMPLETED' AND OLD.objective_status != 'COMPLETED'
                THEN date('now', 'localtime')
            WHEN NEW.objective_status != 'COMPLETED'
                THEN NULL
            ELSE OLD.objective_completed
        END
    WHERE objective_id = NEW.objective_id;
END;