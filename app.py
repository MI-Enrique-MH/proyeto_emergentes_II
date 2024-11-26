from flask import Flask, render_template,request,redirect,url_for,session,flash
import sqlite3
import re
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'miclavesecreta'

def init_sqlite_db():
    conn = sqlite3.connect("guarderia.db")
    cursor = conn.cursor()
    
    # Crear tabla 'usuarios'
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            username TEXT NOT NULL CHECK (username GLOB 'user-[0-9][0-9][0-9]'),
            password TEXT NOT NULL
        );
        """
    )
    
    # Crear tabla 'Niño'
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Niño (
            id_niño TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            fecha_nacimiento DATE NOT NULL,
            direccion TEXT,
            alergias_con_medicas TEXT,
            grupo_asignado_fk TEXT,
            tutor_asignado_fk TEXT,  -- Se agrega la columna tutor_asignado_fk
            FOREIGN KEY (grupo_asignado_fk) REFERENCES Grupo(id_grupo),
            FOREIGN KEY (tutor_asignado_fk) REFERENCES Tutor(id_tutor)
        );
        """
    )
    
    # Crear tabla 'Tutor'
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Tutor (
            id_tutor TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            telefono INTEGER,
            direccion TEXT,
            relacion_con_el_niño TEXT
        );
        """
    )
    
    # Crear tabla 'Grupo'
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Grupo (
            id_grupo TEXT PRIMARY KEY,
            nombre_grupo TEXT NOT NULL,
            capacidad_maxima TEXT,
            id_cuidador_fk TEXT,
            FOREIGN KEY (id_cuidador_fk) REFERENCES Cuidador(id_cuidador)
        );
        """
    )
    
    # Crear tabla 'Cuidador'
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Cuidador (
            id_cuidador TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            telefono TEXT,
            fecha_contactacion TEXT
        );
        """
    )
    
    # Guardar los cambios y cerrar la conexión
    conn.commit()
    conn.close()

# Llamada para crear las tablas
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

        conn = sqlite3.connect("guarderia.db")
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

        conn = sqlite3.connect("guarderia.db")
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

@app.route("/admin/cuidador/registrar", methods=["GET", "POST"])
@login_required
def registrar_cuidador():
    if request.method == "POST":
        # Obtener datos del formulario
        id_cuidador = request.form["id_cuidador"]
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        telefono = request.form["telefono"]
        fecha_contactacion = request.form["fecha_contactacion"]

        # Validar campos obligatorios
        if not id_cuidador or not nombre or not apellido:
            error = "ID, Nombre y Apellido son obligatorios."
            return render_template("cuidador/registrar.html", error=error)

        # Guardar en la base de datos
        try:
            conn = sqlite3.connect("guarderia.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Cuidador (id_cuidador, nombre, apellido, telefono, fecha_contactacion) VALUES (?, ?, ?, ?, ?)",
                (id_cuidador, nombre, apellido, telefono, fecha_contactacion),
            )
            conn.commit()
            conn.close()
            flash("Cuidador registrado exitosamente.")
            return redirect("/admin/cuidador/lista")
        except sqlite3.IntegrityError:
            error = "El ID del cuidador ya existe."
            return render_template("cuidador/registrar.html", error=error)

    # Mostrar formulario
    return render_template("cuidador/registrar.html")
@app.route("/admin/cuidador/lista")
@login_required
def lista_cuidadores():
    # Conexión a la base de datos
    conn = sqlite3.connect("guarderia.db")
    conn.row_factory = sqlite3.Row  # Esto permite usar nombres de columnas en el HTML
    cursor = conn.cursor()
    
    # Obtener todos los registros de la tabla Cuidador
    cursor.execute("SELECT * FROM Cuidador")
    cuidadores = cursor.fetchall()
    conn.close()
    
    # Renderizar la plantilla con los datos de los cuidadores
    return render_template("cuidador/lista.html", cuidadores=cuidadores)

@app.route("/admin/grupo/registrar", methods=["GET", "POST"])
@login_required
def registrar_grupo():
    if request.method == "POST":
        id_grupo = request.form['id_grupo']
        nombre_grupo = request.form['nombre_grupo']
        capacidad_maxima = request.form['capacidad_maxima']
        id_cuidador_fk = request.form['id_cuidador_fk']

        # Guardar el grupo en la base de datos
        conn = sqlite3.connect("guarderia.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Grupo (id_grupo, nombre_grupo, capacidad_maxima, id_cuidador_fk)
            VALUES (?, ?, ?, ?)
        """, (id_grupo, nombre_grupo, capacidad_maxima, id_cuidador_fk))
        conn.commit()
        conn.close()

        flash("Grupo registrado exitosamente")
        return redirect("/admin/grupo/lista")

    # Obtener los cuidadores existentes
    conn = sqlite3.connect("guarderia.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id_cuidador, nombre, apellido FROM Cuidador")
    cuidadores = cursor.fetchall()
    conn.close()

    return render_template("grupo/registrar.html", cuidadores=cuidadores)


@app.route("/admin/grupo/lista")
@login_required
def lista_grupos():
    conn = sqlite3.connect("guarderia.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.id_grupo, g.nombre_grupo, g.capacidad_maxima, 
               c.nombre || ' ' || c.apellido AS cuidador
        FROM Grupo g
        LEFT JOIN Cuidador c ON g.id_cuidador_fk = c.id_cuidador
    """)
    grupos = cursor.fetchall()
    conn.close()

    return render_template("grupo/lista.html", grupos=grupos)

@app.route("/admin/tutor/registrar", methods=["GET", "POST"])
@login_required
def registrar_tutor():
    if request.method == "POST":
        id_tutor = request.form["id_tutor"]
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        telefono = request.form["telefono"]
        direccion = request.form["direccion"]
        relacion_con_el_niño = request.form["relacion_con_el_niño"]

        # Validar campos obligatorios
        if not id_tutor or not nombre or not apellido:
            error = "ID, Nombre y Apellido son obligatorios."
            return render_template("tutor/registrar.html", error=error)

        # Guardar en la base de datos
        try:
            conn = sqlite3.connect("guarderia.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO Tutor (id_tutor, nombre, apellido, telefono, direccion, relacion_con_el_niño)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (id_tutor, nombre, apellido, telefono, direccion, relacion_con_el_niño),
            )
            conn.commit()
            conn.close()
            flash("Tutor registrado exitosamente.")
            return redirect("/admin/tutor/lista")
        except sqlite3.IntegrityError:
            error = "El ID del tutor ya existe."
            return render_template("tutor/registrar.html", error=error)

    # Mostrar formulario
    return render_template("tutor/registrar.html")


@app.route("/admin/tutor/lista")
@login_required
def lista_tutores():
    conn = sqlite3.connect("guarderia.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Tutor")
    tutores = cursor.fetchall()
    conn.close()

    return render_template("tutor/lista.html", tutores=tutores)



@app.route("/admin/nino/registrar", methods=["GET", "POST"])
@login_required
def registrar_nino():
    if request.method == "POST":
        id_niño = request.form["id_niño"]
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        fecha_nacimiento = request.form["fecha_nacimiento"]
        direccion = request.form["direccion"]
        alergias_con_medicas = request.form["alergias_con_medicas"]
        grupo_asignado_fk = request.form["grupo_asignado_fk"]
        tutor_asignado_fk = request.form["tutor_asignado_fk"]

        # Validar campos obligatorios
        if not id_niño or not nombre or not apellido or not fecha_nacimiento:
            error = "ID, Nombre, Apellido y Fecha de Nacimiento son obligatorios."
            return render_template("nino/registrar.html", error=error)

        # Guardar en la base de datos
        try:
            conn = sqlite3.connect("guarderia.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO Niño (id_niño, nombre, apellido, fecha_nacimiento, direccion, alergias_con_medicas, grupo_asignado_fk, tutor_asignado_fk)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (id_niño, nombre, apellido, fecha_nacimiento, direccion, alergias_con_medicas, grupo_asignado_fk, tutor_asignado_fk),
            )
            conn.commit()
            conn.close()
            flash("Niño registrado exitosamente.")
            return redirect("/admin/nino/lista")
        except sqlite3.IntegrityError:
            error = "El ID del niño ya existe."
            return render_template("nino/registrar.html", error=error)

    # Obtener tutores y grupos disponibles
    conn = sqlite3.connect("guarderia.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id_tutor, nombre || ' ' || apellido AS nombre_completo FROM Tutor")
    tutores = cursor.fetchall()
    cursor.execute("""
        SELECT g.id_grupo, g.nombre_grupo, c.nombre || ' ' || c.apellido AS encargado
        FROM Grupo g
        LEFT JOIN Cuidador c ON g.id_cuidador_fk = c.id_cuidador
    """)
    grupos = cursor.fetchall()
    conn.close()

    return render_template("nino/registrar.html", tutores=tutores, grupos=grupos)


@app.route("/admin/nino/lista")
@login_required
def lista_ninos():
    conn = sqlite3.connect("guarderia.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.id_niño, n.nombre, n.apellido, n.fecha_nacimiento, n.direccion, 
               n.alergias_con_medicas, g.nombre_grupo, 
               t.nombre || ' ' || t.apellido AS tutor_asignado,
               c.nombre || ' ' || c.apellido AS cuidador_encargado
        FROM Niño n
        LEFT JOIN Grupo g ON n.grupo_asignado_fk = g.id_grupo
        LEFT JOIN Cuidador c ON g.id_cuidador_fk = c.id_cuidador
        LEFT JOIN Tutor t ON t.id_tutor = (
            SELECT id_tutor FROM Tutor WHERE Tutor.id_tutor = n.id_niño LIMIT 1
        )
    """)
    ninos = cursor.fetchall()
    conn.close()

    return render_template("nino/lista.html", ninos=ninos)


if __name__ == "__main__":
    app.run(debug=True)