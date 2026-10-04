
PRAGMA foreign_keys = ON;

.read "Table Crucibles.sql"
.read 02_views.sql
.read 03_triggers.sql
.read 04_seed.sql

-- sqlite3 pomodoro_tracker.db ".read Create Tables.sql"