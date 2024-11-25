from flask import Flask, render_template,request,redirect,url_for,session,flash
import sqlite3
import re
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'miclavesecreta'

def init_sqlite_db():
    conn = sqlite3.connect("inventarios.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    username TEXT NOT NULL CHECK (username GLOB 'user-[0-9][0-9][0-9]'),
    password TEXT NOT NULL
)
        """
    )
    conn.commit()
    conn.close()

init_sqlite_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        nombre = request.form['nombre']
        username = request.form['username']
        password = request.form['password']

        # Validar el formato del username
        if not re.match(r'^user-\d{3}$', username):
            error = "El formato de username debe ser user-###"
            return render_template("auth/register.html", error=error)

        password_encriptado = generate_password_hash(password)

        conn = sqlite3.connect("inventarios.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios(nombre,username,password) VALUES (?,?,?)",(nombre,username,password_encriptado))
        conn.commit()
        conn.close()

        flash("solo personal autorizado")

        return redirect("/login")

    return render_template("auth/register.html")

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("inventarios.db")
        #resultado de la consulta sea diccionario
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE username = ? ",(username,))
        usuario = cursor.fetchone()
        conn.close()

        if usuario and check_password_hash(usuario['password'],password):
            session['user_id'] = usuario['id']
            return redirect('/admin/dashboard')

    return render_template("auth/login.html")

@app.route("/logout")
def logout():
    session.pop('user_id',None)
    return redirect("/")


@app.route("/admin/dashboard")
@login_required
def dashboard():
    return render_template("admin/dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)