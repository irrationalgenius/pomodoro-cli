
-- The Strategic Layer
DROP TABLE IF EXISTS crucibles CASCADE;
CREATE TABLE crucibles (
    crucible_id        SERIAL PRIMARY KEY,
    crucible_keyword   TEXT NOT NULL UNIQUE,
    crucible_directive TEXT NOT NULL,
    crucible_text      TEXT
);