from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_mysqldb import MySQL
from datetime import datetime, date
import pywhatkit
import pyautogui as pg
from time import sleep
from datetime import datetime, timedelta


# pywhatkit.sendwhatmsg("+543462632986", "hi", 15,10)
def mandar_mensaje(num: str, sms: str):
    """
     envia el mensaje a ese numero lo ingresando en el 2do parametro
    mediante la aplicacion de whatapp desde la web ,luego se cierra automaticamente.
    """

    pywhatkit.sendwhatmsg_instantly(num, sms)
    sleep(3)
    pg.hotkey('ctrl', 'w')


app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'flasksitio'
mysql = MySQL(app)

# para proteger la session,memoria del servidor
app.secret_key = 'mysecretkey'


@app.route('/')
def index():
    if 'username' in session:
        # print(session["username"])
        return redirect(url_for('menu'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        username1 = request.form["usuario"]
        password1 = request.form["password"]
        cur.execute(
            f'SELECT adminname FROM admins WHERE adminname="{username1}" AND adminpassword="{password1}" ')
        adminname = cur.fetchall()

        if adminname:

            session['username'] = request.form['usuario']
            flash(f"usuario logueado: {username1}")
            return redirect(url_for('index'))
        flash("usuario o contraseña incorrecta")
    return render_template('login.html')


@app.route("/menu")
def menu():
    if 'username' in session:
        cur = mysql.connection.cursor()
        cur.execute('select * from contactos ORDER BY id DESC LIMIT 10')
        data = cur.fetchall()
        return render_template('index.html', contactos=data)
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)

    flash("Usuario deslogueado con exito")
    return redirect(url_for('login'))


@app.route("/agregar_contacto", methods=['POST'])
def agregar_contacto():

    if request.method == 'POST':
        _nombrecompleto = request.form['fullname']
        _telefono = int(request.form['phone'].replace(" ", ""))
        _email = request.form['email'].replace(" ", "")
        now = datetime.now()

        if len(_nombrecompleto) <= 60 and len(str(-_telefono)) <= 12 and len(_email) <= 60:

            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO contactos (id,nombrecompleto,telefono,email,fechacreacion) VALUES (NULL,%s,%s,%s,%s)',
                        (_nombrecompleto, _telefono, _email, now))
            mysql.connection.commit()

            # envia mensaje en la pagina
            flash('contacto agregado correctamente')
        else:
            flash('ERROR:valor de un campo ingresado demasiado largo o incorrecto')
            return redirect('/menu')
    return redirect('/menu')


@app.route("/editar_contacto/<id>")
def editar_contacto(id):
    cur = mysql.connection.cursor()
    cur.execute(f'SELECT * FROM contactos where id={id}')
    data = cur.fetchall()

    return render_template('/editar_contacto.html', contacto=data[0])


@app.route("/actualizar_contacto/<id>", methods=["POST"])
def actualizar_contacto(id):

    if request.method == 'POST':
        _nombrecompleto = request.form['fullname']
        _telefono = request.form['phone']
        _email = request.form['email']

        if len(_nombrecompleto) <= 60 and len((_telefono)) <= 12 and len(_email) <= 60:
            cur = mysql.connection.cursor()
            cur.execute("""
            UPDATE contactos
            SET nombrecompleto = %s,
                telefono = %s,
                email = %s
            WHERE id = %s
            """, (_nombrecompleto, _telefono, _email, id))
            mysql.connection.commit()
            flash('contacto actualizado satisfactoriamente')
            return redirect(url_for('menu'))
        else:
            flash('ERROR:no se actualizo contacto')
            return redirect(url_for('menu'))
    else:
        return redirect(url_for('menu'))


@app.route("/eliminar_contacto/<string:id>")
def eliminar_contacto(id):
    cur = mysql.connection.cursor()
    cur.execute(f'SELECT * FROM contactos WHERE id={id}')
    data = cur.fetchall()
    cur.execute(f'DELETE FROM contactos WHERE id={id}')
    mysql.connection.commit()
    flash(f'el cliente"{data[0][1]}" ha sido eliminado')
    return redirect('/menu')


# ====================================TURNOS===========================================


@app.route('/turnos')
def turnos():

    if 'username' in session:
        now = datetime.now()
        cur = mysql.connection.cursor()
        cur.execute(
            f'select * from turnos WHERE fechaturno>="{now.date()}" ORDER BY fechaturno ASC,desde ASC LIMIT 20 ')
        data = cur.fetchall()
        cur.execute('select nombrecompleto from contactos')
        nombres = cur.fetchall()
        return render_template('turnos.html', registros=data, listanombres=nombres)
    return redirect(url_for('login'))


@app.route("/eliminar_turno/<int:id>")
def eliminar_turno(id):
    cur = mysql.connection.cursor()
    cur.execute(f'SELECT * FROM turnos WHERE idturno={id}')
    data = cur.fetchall()
    cur.execute(f'DELETE FROM turnos WHERE idturno={id}')
    mysql.connection.commit()
    flash(f'el turno de:"{data[0][1]}" ha sido eliminado')
    return redirect("/turnos")


@app.route("/mandar_whatapp/<contactonombrecompleto>")
def mandar_whatapp(contactonombrecompleto):

    cur = mysql.connection.cursor()
    cur.execute(
        f'select telefono from contactos WHERE nombrecompleto="{contactonombrecompleto}"')
    data = cur.fetchone()
    cur.execute(
        f'select fechaturno from turnos WHERE contactonombrecompleto="{contactonombrecompleto}"')
    data2 = cur.fetchone()

    mandar_mensaje(
        "+54"+str(data[0]), f"Aviso recordatorio de su turno para el dia:{str(data2[0])}")

    return redirect('/turnos')


@app.route('/agregar_turno', methods=["GET", "POST"])
def agregar_turno():

    if request.method == 'POST' and 'username' in session:
        contactonombrecompleto = request.form['nombrecompleto']
        fechacreacionturno = datetime.now()
        fechaturno = request.form['fechaturno']
        desde_str = request.form['desde']
        hasta = request.form['hasta']
        observaciones = request.form['observaciones']
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO turnos (idturno,contactonombrecompleto,fechacreacionturno,fechaturno,desde,hasta,observaciones) VALUES (NULL,%s,%s,%s,%s,%s,%s)',
                    (contactonombrecompleto, fechacreacionturno, fechaturno, desde_str, hasta, observaciones))
        mysql.connection.commit()
        flash('turno agregado exitosamente')
    return redirect('/turnos')


@app.route("/mandar_whatapps")
def mandar_whatapps():
    if 'username' in session:
        now = datetime.now()
        cur = mysql.connection.cursor()
        fecha_siguiente = now.date() + timedelta(days=1)
        cur.execute(
            f'SELECT contactonombrecompleto FROM turnos WHERE fechaturno="{fecha_siguiente}"')

        nombres_tunos = cur.fetchall()

        for nombre in nombres_tunos:
            cur.execute(
                f'SELECT telefono FROM contactos WHERE nombrecompleto="{nombre[0]}"')
            telefono = cur.fetchone()

            mandar_mensaje(
                "+54"+str(telefono[0]), f"automensaje:aviso recordatorio de su turno para el dia {fecha_siguiente}")

    return redirect("/turnos")


@app.route("/editar_turno/<int:id>")
def editar_turno(id):
    if 'username' in session:
        cur = mysql.connection.cursor()
        cur.execute(f'SELECT * FROM turnos where idturno={id}')
        data = cur.fetchall()

        return render_template('/editar_turno.html', registro=data[0])
    return redirect(url_for('login'))


@app.route("/actualizar_turno/<id>", methods=["POST"])
def actualizar_turno(id):

    if request.method == 'POST':
        _nombrecompleto = request.form['nombrecompleto']
        _fechaturno = request.form['fechaturno']
        _desde = request.form['desde']
        _hasta = request.form['hasta']
        _observaciones = request.form['observaciones']

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE turnos
            SET contactonombrecompleto = %s,
                fechaturno = %s,
                desde = %s,
                hasta = %s,
                observaciones = %s
            WHERE idturno = %s
            """, (_nombrecompleto, _fechaturno, _desde, _hasta, _observaciones, id))
        mysql.connection.commit()
        flash('contacto actualizado satisfactoriamente')
    return redirect(url_for('turnos'))


@app.route("/presentacion")
def presentacion():
    return render_template("presentacion.html")


if __name__ == "__main__":
    app.run(port=3000, debug=True)
