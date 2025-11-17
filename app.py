import sqlite3
from flask import Flask, g, render_template, request, redirect, url_for, session, flash

DATABASE = "hw13.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "change_this_in_real_life"  # 作业用就这样即可


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def login_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in first.")
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # 作业要求账号密码
        if username == "admin" and password == "password":
            session["logged_in"] = True
            flash("Logged in successfully.")
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()

    students = db.execute(
        "SELECT id, first_name, last_name FROM students ORDER BY id"
    ).fetchall()

    quizzes = db.execute(
        "SELECT id, subject, num_questions, quiz_date FROM quizzes ORDER BY id"
    ).fetchall()

    return render_template(
        "dashboard.html",
        students=students,
        quizzes=quizzes,
    )


@app.route("/student/add", methods=["GET", "POST"])
@login_required
def add_student():
    error = None
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()

        if not first_name or not last_name:
            error = "First name and last name are required."
        else:
            try:
                db = get_db()
                db.execute(
                    "INSERT INTO students (first_name, last_name) VALUES (?, ?)",
                    (first_name, last_name),
                )
                db.commit()
                flash("Student added successfully.")
                return redirect(url_for("dashboard"))
            except Exception as e:
                error = f"Failed to add student: {e}"

    return render_template("add_student.html", error=error)


@app.route("/quiz/add", methods=["GET", "POST"])
@login_required
def add_quiz():
    error = None
    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        num_questions = request.form.get("num_questions", "").strip()
        quiz_date = request.form.get("quiz_date", "").strip()  # HTML date input: YYYY-MM-DD

        if not subject or not num_questions or not quiz_date:
            error = "All fields are required."
        else:
            try:
                num_questions_int = int(num_questions)
                db = get_db()
                db.execute(
                    "INSERT INTO quizzes (subject, num_questions, quiz_date) VALUES (?, ?, ?)",
                    (subject, num_questions_int, quiz_date),
                )
                db.commit()
                flash("Quiz added successfully.")
                return redirect(url_for("dashboard"))
            except ValueError:
                error = "Number of questions must be an integer."
            except Exception as e:
                error = f"Failed to add quiz: {e}"

    return render_template("add_quiz.html", error=error)


@app.route("/student/<int:student_id>")
@login_required
def student_results(student_id):
    db = get_db()

    student = db.execute(
        "SELECT id, first_name, last_name FROM students WHERE id = ?", (student_id,)
    ).fetchone()

    if student is None:
        flash("Student not found.")
        return redirect(url_for("dashboard"))

    results = db.execute(
        """
        SELECT r.id AS result_id,
               r.score,
               q.id AS quiz_id,
               q.subject,
               q.quiz_date
        FROM results r
        JOIN quizzes q ON r.quiz_id = q.id
        WHERE r.student_id = ?
        ORDER BY q.id
        """,
        (student_id,),
    ).fetchall()

    return render_template(
        "student_results.html",
        student=student,
        results=results,
    )


@app.route("/results/add", methods=["GET", "POST"])
@login_required
def add_result():
    db = get_db()
    error = None

    students = db.execute(
        "SELECT id, first_name, last_name FROM students ORDER BY id"
    ).fetchall()
    quizzes = db.execute(
        "SELECT id, subject, quiz_date FROM quizzes ORDER BY id"
    ).fetchall()

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        quiz_id = request.form.get("quiz_id", "").strip()
        score = request.form.get("score", "").strip()

        if not student_id or not quiz_id or not score:
            error = "All fields are required."
        else:
            try:
                student_id_int = int(student_id)
                quiz_id_int = int(quiz_id)
                score_int = int(score)
                if score_int < 0 or score_int > 100:
                    error = "Score must be between 0 and 100."
                else:
                    db.execute(
                        "INSERT INTO results (student_id, quiz_id, score) VALUES (?, ?, ?)",
                        (student_id_int, quiz_id_int, score_int),
                    )
                    db.commit()
                    flash("Result added successfully.")
                    return redirect(url_for("dashboard"))
            except ValueError:
                error = "Student, quiz and score must be integers."
            except Exception as e:
                error = f"Failed to add result: {e}"

    return render_template(
        "add_result.html",
        error=error,
        students=students,
        quizzes=quizzes,
    )



@app.route("/quiz/<int:quiz_id>/results")
def quiz_results_public(quiz_id):
    db = get_db()

    quiz = db.execute(
        "SELECT id, subject, quiz_date FROM quizzes WHERE id = ?", (quiz_id,)
    ).fetchone()
    if quiz is None:
        flash("Quiz not found.")
        return redirect(url_for("login"))

    results = db.execute(
        """
        SELECT r.student_id,
               r.score
        FROM results r
        WHERE r.quiz_id = ?
        ORDER BY r.student_id
        """,
        (quiz_id,),
    ).fetchall()

    return render_template(
        "quiz_results_public.html",
        quiz=quiz,
        results=results,
    )


if __name__ == "__main__":
    app.run(debug=True)
