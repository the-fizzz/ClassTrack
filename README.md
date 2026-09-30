# ClassTrack — Bilingual Attendance System

This version keeps the original Flask + SQLite attendance system and adds:
- English / Japanese language switcher
- Language preference stored in the Flask session
- Japanese UI translations for login, dashboard, students, attendance, and reports
- Japanese date formatting
- Bilingual Chart.js labels
- Existing attendance database schema preserved

## Run

Open Terminal in this project folder:

```bash
python3 app.py
```

Then open:

http://127.0.0.1:5001

Login:
- Username: teacher
- Password: 1234

The language switcher is in the sidebar and on the login page.

## Important

`attendance.db` is preserved. The attendance statuses stored in the database remain:
`Present`, `Absent`, `Late`, `Excused`.

Only the displayed UI language changes.
