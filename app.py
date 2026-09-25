from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import secrets
import string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "V1-DEMO-CHANGE-IN-PRODUCTION"
DB = "emgepron.db"

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            om TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Gestor OM',
            password_hash TEXT NOT NULL,
            must_change_password INTEGER NOT NULL DEFAULT 0,
            two_factor_enabled INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Ativo'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            name TEXT,
            om TEXT,
            category TEXT,
            status TEXT,
            assets INTEGER DEFAULT 0,
            co2 REAL DEFAULT 0,
            renewable REAL DEFAULT 0,
            diesel REAL DEFAULT 0,
            value REAL DEFAULT 0
        )
    """)
    admin = conn.execute("SELECT id FROM users WHERE email = ?", ("admin@emgepron.local",)).fetchone()
    if not admin:
        conn.execute("""
            INSERT INTO users
            (name,email,om,role,password_hash,two_factor_enabled)
            VALUES (?,?,?,?,?,?)
        """, (
            "Administrador EMGEPRON",
            "admin@emgepron.local",
            "EMGEPRON",
            "Administrador EMGEPRON",
            generate_password_hash("Admin@123"),
            1
        ))
    count = conn.execute("SELECT COUNT(*) AS n FROM projects").fetchone()["n"]
    if count == 0:
        sample = [
            ("IR-001","Ilha Rasa","CAMR","Transição Energética","Em implantação",4,33.2,58,12450,450000),
            ("SO-002","Usina Solar OM X","OM X","Energia Renovável","Em operação",12,5480,24500,0,8200000),
            ("EE-003","Eficiência Energética","OM Y","Eficiência Energética","Em planejamento",3,1120,2300,320000,1600000),
            ("BI-004","Recuperação Ambiental","OM Z","Biodiversidade","Em desenvolvimento",7,850,0,0,720000),
            ("CO-005","Gestão de Resíduos","Base Naval A","Resíduos","Em implantação",5,420,0,0,310000),
        ]
        conn.executemany("""
            INSERT INTO projects
            (code,name,om,category,status,assets,co2,renewable,diesel,value)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, sample)
    conn.commit()
    conn.close()

def current_user():
    if "user_id" not in session:
        return None
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()
    return user

def temp_password():
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(12))

@app.route("/")
def index():
    if current_user():
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        om = request.form.get("om", "").strip()

        if not name or not email or not om:
            flash("Preencha todos os campos.", "error")
            return redirect(url_for("register"))

        if not email.endswith((".mil.br", "@marinha.mil.br")):
            # V1 demo: accepts institutional-looking addresses only.
            if "@" not in email:
                flash("Informe um e-mail válido.", "error")
                return redirect(url_for("register"))

        password = temp_password()
        conn = db()
        try:
            conn.execute("""
                INSERT INTO users
                (name,email,om,role,password_hash,must_change_password,two_factor_enabled)
                VALUES (?,?,?,?,?,?,?)
            """, (
                name, email, om, "Gestor OM",
                generate_password_hash(password), 1, 0
            ))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            flash("Este e-mail já possui cadastro.", "error")
            return redirect(url_for("register"))
        conn.close()

        # V1: simula o envio do e-mail. Em produção, integrar SMTP/serviço institucional.
        session["demo_temp_password"] = password
        session["demo_email"] = email
        return render_template("temp_password.html", email=email, password=password)

    return render_template("register.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        flash("E-mail ou senha inválidos.", "error")
        return redirect(url_for("index"))

    if user["status"] != "Ativo":
        flash("Usuário bloqueado ou inativo.", "error")
        return redirect(url_for("index"))

    session["user_id"] = user["id"]

    if user["must_change_password"]:
        return redirect(url_for("change_password"))

    return redirect(url_for("dashboard"))

@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    user = current_user()
    if not user:
        return redirect(url_for("index"))

    if request.method == "POST":
        new_password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if len(new_password) < 8 or new_password != confirm:
            flash("A senha deve ter pelo menos 8 caracteres e os campos devem coincidir.", "error")
            return redirect(url_for("change_password"))

        conn = db()
        conn.execute("""
            UPDATE users SET password_hash=?, must_change_password=0, two_factor_enabled=1
            WHERE id=?
        """, (generate_password_hash(new_password), user["id"]))
        conn.commit()
        conn.close()
        flash("Senha atualizada. 2FA habilitado para este usuário.", "success")
        return redirect(url_for("dashboard"))

    return render_template("change_password.html", user=user)

@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("index"))

    conn = db()
    projects = conn.execute("SELECT * FROM projects ORDER BY id").fetchall()
    conn.close()

    totals = {
        "projects": len(projects),
        "assets": sum(p["assets"] for p in projects),
        "co2": sum(p["co2"] for p in projects),
        "renewable": sum(p["renewable"] for p in projects),
        "diesel": sum(p["diesel"] for p in projects),
        "value": sum(p["value"] for p in projects),
    }
    return render_template("dashboard.html", user=user, projects=projects, totals=totals)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
