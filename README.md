# pomodoro-cli

Small application for tracking pomodoro events overtime.

Using SQLite database

sqlite3 -cmd ".read Deploy.sql" pomodoros.sqlite ".exit"
sqlite3 db/pomodoros.sqlite ".schema" > db/schema.sql
sqlite3 db/pomodoros.sqlite ".dump" > db/schema.sql
python -c "import sqlite3; conn = sqlite3.connect('pomodoros.sqlite'); conn.close()"