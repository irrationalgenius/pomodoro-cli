
-- The Strategic Layer
CREATE TABLE crucibles (
    crucible_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    crucible_keyword   TEXT NOT NULL UNIQUE,
    crucible_directive TEXT NOT NULL,
    crucible_text      TEXT
);