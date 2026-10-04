# pomodoro-cli

Small application for tracking pomodoro events overtime.

Using SQLite database

sqlite3 -cmd ".read Deploy.sql" pomodoros.sqlite ".exit"
sqlite3 pomodoros.sqlite ".schema" > schema.sql