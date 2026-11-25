import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret-key-before-deployment")
db_url = os.getenv("DATABASE_URL", "sqlite:///aptitudelearner.db")
if db_url.startswith("mysql://"):
    db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to continue."

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attempts = db.relationship("Attempt", backref="user", lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(40), nullable=False, index=True)
    topic = db.Column(db.String(80), nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(300), nullable=False)
    option_b = db.Column(db.String(300), nullable=False)
    option_c = db.Column(db.String(300), nullable=False)
    option_d = db.Column(db.String(300), nullable=False)
    answer = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text, nullable=False)

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(40), nullable=False)
    total = db.Column(db.Integer, nullable=False)
    correct = db.Column(db.Integer, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    duration_seconds = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

SEED = [
    ("Aptitude","Percentage","A product costs ₹800. Its price increases by 15%. What is the new price?","₹900","₹920","₹940","₹960","B","15% of ₹800 is ₹120. Add it to ₹800 to get ₹920."),
    ("Aptitude","Profit and Loss","A bag is bought for ₹500 and sold for ₹600. What is the profit percentage?","10%","15%","20%","25%","C","Profit = ₹100. (100 ÷ 500) × 100 = 20%."),
    ("Aptitude","Average","Find the average of 12, 18 and 24.","16","18","20","22","B","(12 + 18 + 24) ÷ 3 = 18."),
    ("Aptitude","Time and Work","Five workers finish a job in 12 days. How many days will 10 workers take at the same rate?","3","6","8","10","B","Doubling the workforce halves the time: 12 ÷ 2 = 6 days."),
    ("Aptitude","Speed Distance","A car travels 150 km in 3 hours. What is its average speed?","40 km/h","45 km/h","50 km/h","60 km/h","C","Speed = distance ÷ time = 150 ÷ 3 = 50 km/h."),
    ("Aptitude","Ratio","The ratio of two numbers is 3:5 and their sum is 40. What is the smaller number?","12","15","18","25","B","Total parts = 8. One part = 5, so the smaller number is 15."),
    ("Reasoning","Number Series","Find the next number: 2, 6, 18, 54, __","108","126","162","216","C","Each term is multiplied by 3. 54 × 3 = 162."),
    ("Reasoning","Coding Decoding","If CAT is coded as DBU by shifting each letter one place forward, how is DOG coded?","EPH","EOG","FPH","DPI","A","D→E, O→P and G→H. DOG becomes EPH."),
    ("Reasoning","Direction Sense","A person walks 4 km east and then 3 km west. Where are they from the starting point?","1 km east","1 km west","7 km east","7 km west","A","The net movement is 4 − 3 = 1 km east."),
    ("Reasoning","Blood Relations","A is the brother of B. B is the mother of C. How is A related to C?","Father","Uncle","Brother","Grandfather","B","A is the brother of C's mother, so A is C's uncle."),
    ("Verbal","Synonyms","Choose the word closest in meaning to 'Rapid'.","Slow","Quick","Weak","Late","B","Rapid means fast or quick."),
    ("Verbal","Antonyms","Choose the opposite of 'Expand'.","Enlarge","Extend","Contract","Increase","C","Contract means to become smaller."),
    ("Verbal","Sentence Correction","Choose the grammatically correct sentence.","She go to college.","She going to college.","She goes to college.","She gone to college.","C","With 'she' in the simple present tense, use 'goes'."),
    ("Verbal","Prepositions","Choose the correct preposition: She is interested ___ music.","on","at","in","for","C","The standard expression is 'interested in'."),
    ("Programming","Java","Which keyword is used to inherit a class in Java?","implements","extends","inherits","super","B","Java uses the extends keyword for class inheritance."),
    ("Programming","Python","Which Python data type stores key-value pairs?","List","Tuple","Dictionary","Set","C","A dictionary stores data as key-value pairs."),
    ("Programming","SQL","Which SQL command retrieves data from a table?","INSERT","UPDATE","SELECT","DELETE","C","SELECT retrieves rows from database tables."),
    ("Programming","C Programming","Which symbol ends most C statements?","; ",":",".",",","A","A semicolon terminates most C statements."),
    ("Programming","OOP","Which OOP concept bundles data and methods together?","Inheritance","Encapsulation","Polymorphism","Abstraction","B","Encapsulation combines data and methods and controls access to state."),
    ("Interview","HR Interview","Which is the best approach when answering 'Tell me about yourself'?","Share unrelated personal details","Give a concise education, skills and goal summary","Read your entire resume","Discuss salary first","B","Give a focused professional introduction relevant to the role."),
    ("Interview","DBMS","What does DBMS stand for?","Data Backup Management System","Database Management System","Digital Base Management Service","Database Memory Storage","B","DBMS stands for Database Management System."),
    ("Interview","Operating Systems","Which component manages processes and memory?","Compiler","Kernel","Browser","Editor","B","The operating system kernel manages core resources such as processes and memory."),
    ("Interview","Computer Networks","What does HTTP stand for?","HyperText Transfer Protocol","High Transfer Text Process","Hyperlink Terminal Transfer Program","Host Text Transfer Protocol","A","HTTP is HyperText Transfer Protocol."),
    ("Programming","Java","Which method is the entry point of a standard Java application?","start()","run()","main()","init()","C","The JVM starts a standard Java application by invoking main()."),
]

@app.cli.command("seed")
def seed():
    if Question.query.count() == 0:
        for row in SEED:
            db.session.add(Question(category=row[0], topic=row[1], question=row[2],
                option_a=row[3], option_b=row[4], option_c=row[5], option_d=row[6],
                answer=row[7], explanation=row[8]))
        db.session.commit()
        print(f"Inserted {len(SEED)} sample questions.")
    else:
        print("Question bank already contains data; no seed changes made.")

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter your name, a valid email and a password with at least 6 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with this email already exists. Please log in.", "error")
        else:
            user = User(name=name, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Your account is ready. Welcome to AptitudeLearner!", "success")
            return redirect(url_for("dashboard"))
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Email or password is incorrect.", "error")
    return render_template("auth.html", mode="login")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    attempts = Attempt.query.filter_by(user_id=current_user.id).order_by(Attempt.created_at.desc()).all()
    total_tests = len(attempts)
    best = max((a.accuracy for a in attempts), default=0)
    avg = sum(a.accuracy for a in attempts) / total_tests if total_tests else 0
    total_questions = sum(a.total for a in attempts)
    recent = attempts[:5]
    return render_template("dashboard.html", total_tests=total_tests, best=round(best),
        avg=round(avg), total_questions=total_questions, recent=recent)

@app.route("/practice")
@login_required
def practice():
    categories = ["Aptitude", "Reasoning", "Verbal", "Programming", "Interview"]
    data = {}
    for cat in categories:
        data[cat] = sorted({q.topic for q in Question.query.filter_by(category=cat).all()})
    return render_template("practice.html", categories=categories, data=data)

@app.route("/test")
@login_required
def test():
    return render_template("test.html")

@app.route("/api/questions")
@login_required
def api_questions():
    category = request.args.get("category", "").strip()
    topic = request.args.get("topic", "").strip()
    limit = min(max(request.args.get("limit", 10, type=int), 1), 30)
    query = Question.query
    if category:
        query = query.filter_by(category=category)
    if topic:
        query = query.filter_by(topic=topic)
    questions = query.order_by(db.func.random()).limit(limit).all()
    return jsonify([{"id":q.id,"category":q.category,"topic":q.topic,"question":q.question,
        "options":[q.option_a,q.option_b,q.option_c,q.option_d]} for q in questions])

@app.route("/api/submit", methods=["POST"])
@login_required
def submit():
    payload = request.get_json(silent=True) or {}
    answers = payload.get("answers", {})
    ids = [int(x) for x in answers.keys() if str(x).isdigit()]
    questions = Question.query.filter(Question.id.in_(ids)).all()
    lookup = {q.id:q for q in questions}
    correct = 0
    details = []
    for qid in ids:
        q = lookup.get(qid)
        selected = str(answers.get(str(qid), "")).upper()
        is_correct = bool(q and selected == q.answer)
        if is_correct:
            correct += 1
        if q:
            details.append({"id":q.id,"question":q.question,"selected":selected,
                "correct":q.answer,"is_correct":is_correct,"explanation":q.explanation})
    total = len(details)
    if total == 0:
        return jsonify({"error":"No answers were submitted."}), 400
    title = str(payload.get("title", "Practice Test"))[:120]
    category = str(payload.get("category", "Mixed"))[:40]
    duration = max(0, min(int(payload.get("duration", 0)), 86400))
    accuracy = round(correct / total * 100, 2)
    attempt = Attempt(user_id=current_user.id, title=title, category=category,
        total=total, correct=correct, accuracy=accuracy, duration_seconds=duration)
    db.session.add(attempt)
    db.session.commit()
    return jsonify({"correct":correct,"total":total,"accuracy":accuracy,
        "attempt_id":attempt.id,"details":details})

@app.route("/progress")
@login_required
def progress():
    attempts = Attempt.query.filter_by(user_id=current_user.id).order_by(Attempt.created_at.desc()).all()
    total = sum(a.total for a in attempts)
    correct = sum(a.correct for a in attempts)
    category_stats = {}
    for a in attempts:
        if a.category not in category_stats:
            category_stats[a.category] = {"tests":0,"correct":0,"total":0}
        s = category_stats[a.category]
        s["tests"] += 1; s["correct"] += a.correct; s["total"] += a.total
    for s in category_stats.values():
        s["accuracy"] = round(s["correct"] / s["total"] * 100) if s["total"] else 0
    return render_template("progress.html", attempts=attempts, total=total, correct=correct,
        accuracy=round(correct/total*100) if total else 0, category_stats=category_stats)

@app.route("/bookmarks")
@login_required
def bookmarks():
    return render_template("bookmarks.html")

@app.route("/api/bookmarks", methods=["GET", "POST", "DELETE"])
@login_required
def api_bookmarks():
    # Bookmarks are kept per account in the database via a compact JSON list in the user's session.
    key = f"bookmarks_{current_user.id}"
    ids = request.cookies.get(key, "")
    saved = [int(x) for x in ids.split(",") if x.isdigit()]
    if request.method == "GET":
        qs = Question.query.filter(Question.id.in_(saved)).all() if saved else []
        return jsonify([{"id":q.id,"category":q.category,"topic":q.topic,"question":q.question} for q in qs])
    payload = request.get_json(silent=True) or {}
    qid = int(payload.get("id", 0))
    if not Question.query.get(qid):
        return jsonify({"error":"Question not found"}), 404
    if request.method == "POST" and qid not in saved:
        saved.append(qid)
    if request.method == "DELETE":
        saved = [x for x in saved if x != qid]
    response = jsonify({"saved":True})
    response.set_cookie(key, ",".join(map(str, saved)), httponly=True, samesite="Lax", max_age=31536000)
    return response

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
