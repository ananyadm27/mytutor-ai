from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import ollama
import sqlite3
import datetime
app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            mistakes INTEGER DEFAULT 0
        )
    """)

    c.execute("""
       CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        response TEXT,
        date TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("login.html")

# ---------------- REGISTER PAGE ----------------
@app.route("/register")
def register_page():
    return render_template("register.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = c.fetchone()

    if existing_user:
        conn.close()
        return "Username already exists. Please choose another."

    c.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, password)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("home"))

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    )
    user = c.fetchone()

    conn.close()

    if user:
        session["user"] = username
        return redirect(url_for("chat"))
    else:
        return "Invalid username or password."

# ---------------- CHAT PAGE ----------------
@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect(url_for("home"))

    return render_template("index.html", user=session["user"])

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))

    user = session["user"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Total mistakes
    c.execute("SELECT mistakes FROM users WHERE username=?", (user,))
    result = c.fetchone()
    mistakes = result[0] if result else 0
    c.execute("""SELECT date, COUNT(*) FROM history  WHERE username=?  GROUP BY date
     """, (user,))
    daily_data = c.fetchall()

    # Total messages
    c.execute("SELECT COUNT(*) FROM history WHERE username=?", (user,))
    total_messages = c.fetchone()[0]

    conn.close()

    # Calculate accuracy
    if total_messages > 0:
        correct_messages = total_messages - mistakes
        accuracy = round((correct_messages / total_messages) * 100, 2)
    else:
        correct_messages = 0
        accuracy = 0

    # Performance level
    if accuracy >= 80:
        performance = "Excellent 🌟"
    elif accuracy >= 50:
        performance = "Improving 👍"
    else:
        performance = "Needs Practice 📘"

    return render_template(
        "dashboard.html",
        user=user,
        mistakes=mistakes,
        total_messages=total_messages,
        correct_messages=correct_messages,
        accuracy=accuracy,
        performance=performance,
        daily_data=daily_data
    )


# ---------------- HISTORY ----------------
@app.route("/history")
def history():
    if "user" not in session:
        return redirect(url_for("home"))

    user = session["user"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "SELECT message, response FROM history WHERE username=?",
        (user,)
    )
    records = c.fetchall()

    conn.close()

    return render_template("history.html", records=records)

# ---------------- AI CHAT ----------------
@app.route("/ask", methods=["POST"])
def ask():
    if "user" not in session:
        return jsonify({"reply": "Not logged in."})

    data = request.json
    message = data["message"]
    user = session["user"]

    prompt = f"""
You are an English tutor AI.

1. Answer naturally.
2. Check grammar.
3. If mistake:
   - Correct sentence
   - Explain simply
4. If correct, say grammatically correct.

Student sentence:
{message}
"""

    response = ollama.chat(
        model="mistral",
        messages=[{"role": "user", "content": prompt}]
    )

    reply = response["message"]["content"]

    # Detect grammar correction
    mistake_detected = "Correct sentence" in reply

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if mistake_detected:
        c.execute(
            "UPDATE users SET mistakes = mistakes + 1 WHERE username=?",
            (user,)
        )

   
    today = datetime.date.today().isoformat()

    c.execute(
             "INSERT INTO history (username, message, response, date) VALUES (?, ?, ?, ?)",
              (user, message, reply, today)
         )



    conn.commit()
    conn.close()

    return jsonify({"reply": reply})
@app.route("/reset")
def reset():
    if "user" not in session:
        return redirect(url_for("home"))

    user = session["user"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE users SET mistakes=0 WHERE username=?", (user,))
    c.execute("DELETE FROM history WHERE username=?", (user,))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))
@app.route("/export")
def export():
    if "user" not in session:
        return redirect(url_for("home"))

    user = session["user"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT message, response FROM history WHERE username=?", (user,))
    records = c.fetchall()
    conn.close()

    content = ""
    for msg, res in records:
        content += f"You: {msg}\nTutor: {res}\n\n"

    return content, 200, {
        'Content-Type': 'text/plain',
        'Content-Disposition': 'attachment; filename=chat_history.txt'
    }


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(debug=True)
