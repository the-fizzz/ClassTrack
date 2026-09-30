from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import json
from datetime import date

app = Flask(__name__)
app.secret_key = "secret123"

with open("translations.json", encoding="utf-8") as f:
    TRANSLATIONS = json.load(f)

SUPPORTED_LANGUAGES = ("en", "ja")

def get_language():
    lang = session.get("lang", "en")
    return lang if lang in SUPPORTED_LANGUAGES else "en"

def translate(key):
    lang = get_language()
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )

@app.context_processor
def inject_language():
    return {
        "lang": get_language(),
        "t": translate
    }

@app.route("/set-language/<lang>")
def set_language(lang):
    if lang in SUPPORTED_LANGUAGES:
        session["lang"] = lang
    return redirect(request.referrer or url_for("dashboard"))


# -----------------------
# Database Connection
# -----------------------

def get_db():

    conn = sqlite3.connect("attendance.db")
    conn.row_factory = sqlite3.Row

    return conn


# -----------------------
# Create Tables
# -----------------------

def init_db():

    conn = get_db()

    conn.execute("""

    CREATE TABLE IF NOT EXISTS students(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT NOT NULL

    )

    """)


    conn.execute("""

    CREATE TABLE IF NOT EXISTS attendance(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        student_id INTEGER NOT NULL,

        date TEXT,

        status TEXT,

        UNIQUE(student_id,date)

    )

    """)

    conn.commit()

    conn.close()


init_db()


# -----------------------
# Login Required
# -----------------------

def logged_in():

    return 'user' in session



# -----------------------
# Home
# -----------------------

@app.route('/')

def home():

    if logged_in():

        return redirect('/dashboard')

    return redirect('/login')



# -----------------------
# Login
# -----------------------

@app.route('/login', methods=['GET', 'POST'])

def login():

    if logged_in():

        return redirect('/dashboard')


    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']


        if username == "teacher" and password == "1234":

            session['user'] = username

            return redirect('/dashboard')


    return render_template(

        "login.html"

    )



# -----------------------
# Logout
# -----------------------

@app.route('/logout')

def logout():

    session.clear()

    return redirect('/login')




# -----------------------
# Dashboard
# -----------------------

@app.route('/dashboard')

def dashboard():

    if not logged_in():

        return redirect('/login')


    conn = get_db()


    total = conn.execute(

        "SELECT COUNT(*) FROM students"

    ).fetchone()[0]


    today = str(date.today())


    present = conn.execute(

        """

        SELECT COUNT(*)

        FROM attendance

        WHERE date=?

        AND status='Present'

        """,

        (

            today,

        )

    ).fetchone()[0]



    absent = conn.execute(

        """

        SELECT COUNT(*)

        FROM attendance

        WHERE date=?

        AND status='Absent'

        """,

        (

            today,

        )

    ).fetchone()[0]



    late = conn.execute(

        """

        SELECT COUNT(*)

        FROM attendance

        WHERE date=?

        AND status='Late'

        """,

        (

            today,

        )

    ).fetchone()[0]



    excused = conn.execute(

        """

        SELECT COUNT(*)

        FROM attendance

        WHERE date=?

        AND status='Excused'

        """,

        (

            today,

        )

    ).fetchone()[0]



    conn.close()



    return render_template(

        "dashboard.html",

        total=total,

        present=present,

        absent=absent,

        late=late,

        excused=excused

    )



# -----------------------
# Students Page
# -----------------------

@app.route('/students')

def students():

    if not logged_in():

        return redirect('/login')


    conn = get_db()


    students = conn.execute(

        "SELECT * FROM students"

    ).fetchall()


    conn.close()


    return render_template(

        "students.html",

        students=students

    )

# -----------------------
# Add Student
# -----------------------

@app.route('/add_student', methods=['POST'])

def add_student():

    if not logged_in():

        return redirect('/login')


    name = request.form['name']


    conn = get_db()


    conn.execute(

        "INSERT INTO students(name) VALUES(?)",

        (

            name,

        )

    )


    conn.commit()

    conn.close()


    return redirect('/students')




# -----------------------
# Delete Student
# -----------------------

@app.route('/delete_student/<int:id>')

def delete_student(id):

    if not logged_in():

        return redirect('/login')


    conn = get_db()


    conn.execute(

        "DELETE FROM attendance WHERE student_id=?",

        (

            id,

        )

    )


    conn.execute(

        "DELETE FROM students WHERE id=?",

        (

            id,

        )

    )


    conn.commit()

    conn.close()


    return redirect('/students')




# -----------------------
# Attendance Page
# -----------------------

@app.route('/attendance')

def attendance():

    if not logged_in():

        return redirect('/login')


    conn = get_db()


    students = conn.execute(

        "SELECT * FROM students"

    ).fetchall()


    conn.close()


    return render_template(

        "attendance.html",

        students=students,

        today=str(date.today())

    )




# -----------------------
# Save Attendance
# -----------------------

@app.route('/save_attendance', methods=['POST'])

def save_attendance():

    if not logged_in():

        return redirect('/login')


    selected_date = request.form['date']


    conn = get_db()


    students = conn.execute(

        "SELECT * FROM students"

    ).fetchall()



    for student in students:


        status = request.form.get(

            f"student_{student['id']}",

            "Present"

        )



        existing = conn.execute(

            """

            SELECT id

            FROM attendance

            WHERE student_id=?

            AND date=?

            """,

            (

                student['id'],

                selected_date

            )

        ).fetchone()



        if existing:


            conn.execute(

                """

                UPDATE attendance

                SET status=?

                WHERE id=?

                """,

                (

                    status,

                    existing['id']

                )

            )


        else:


            conn.execute(

                """

                INSERT INTO attendance(

                    student_id,

                    date,

                    status

                )

                VALUES(?,?,?)

                """,

                (

                    student['id'],

                    selected_date,

                    status

                )

            )



    conn.commit()

    conn.close()


    return redirect('/dashboard')




# -----------------------
# Reports
# -----------------------

@app.route('/reports')

def reports():

    if not logged_in():

        return redirect('/login')


    selected_date = request.args.get(

        'date',

        str(date.today())

    )


    conn = get_db()


    report = conn.execute(

        """

        SELECT

            students.name,

            attendance.status


        FROM attendance


        JOIN students


        ON attendance.student_id = students.id


        WHERE attendance.date=?


        """,

        (

            selected_date,

        )

    ).fetchall()



    present = 0
    absent = 0
    late = 0
    excused = 0


    for row in report:


        if row['status'] == "Present":

            present += 1


        elif row['status'] == "Absent":

            absent += 1


        elif row['status'] == "Late":

            late += 1


        elif row['status'] == "Excused":

            excused += 1



    conn.close()



    return render_template(

        "reports.html",

        report=report,

        date=selected_date,

        present=present,

        absent=absent,

        late=late,

        excused=excused

    )




# -----------------------
# Run App
# -----------------------

if __name__ == "__main__":

    app.run(
    host="0.0.0.0",
    port=5001,
    debug=True
)