
-- The Operations Layer
DROP TABLE IF EXISTS objectives CASCADE;
CREATE TABLE objectives (
    objective_id           SERIAL PRIMARY KEY,
    crucible_id            INT REFERENCES crucibles(crucible_id) ON DELETE SET NULL,
    objective_title        TEXT NOT NULL,
    objective_description  TEXT,
    objective_target_date  TIMESTAMP,
    objective_status       TEXT NOT NULL DEFAULT 'ACTIVE'
                           CHECK (objective_status IN ('ACTIVE', 'COMPLETED', 'ON_HOLD', 'ARCHIVED')),
    objective_created      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    objective_updated      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    objective_completed    TIMESTAMP
);

CREATE INDEX idx_objectives_status ON objectives(objective_status);
CREATE INDEX idx_objectives_target ON objectives(objective_target_date);

CREATE OR REPLACE FUNCTION trg_objectives_lifecycle_func()
RETURNS TRIGGER AS $$
BEGIN
    NEW.objective_updated = CURRENT_TIMESTAMP;
    IF NEW.objective_status = 'COMPLETED' AND OLD.objective_status != 'COMPLETED' THEN
        NEW.objective_completed = CURRENT_DATE;
    ELSIF NEW.objective_status != 'COMPLETED' THEN
        NEW.objective_completed = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_objectives_lifecycle
BEFORE UPDATE OF objective_status ON objectives
FOR EACH ROW
EXECUTE FUNCTION trg_objectives_lifecycle_func();