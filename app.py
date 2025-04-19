from flask import Flask, render_template, request, redirect, session, send_from_directory
import pymysql
import os
from flask_session import Session

app = Flask(__name__)

# Configurações da sessão
app.config['SECRET_KEY'] = 'chave-super-secreta'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

UPLOAD_FOLDER = 'static/livros'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def connect_to_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="biblioteca",
        cursorclass=pymysql.cursors.Cursor
    )


@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM livros")
    livros = cursor.fetchall()
    conn.close()
    return render_template('index.html', livros=livros)


@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    if 'usuario_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        pdf_file = request.files['pdf']
        
        caminho_pdf = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
        pdf_file.save(caminho_pdf)

        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO livros (titulo, descricao, caminho_pdf)
            VALUES (%s, %s, %s)
        """, (titulo, descricao, pdf_file.filename))

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('adicionar.html')


@app.route('/deletar/<int:id>', methods=['GET'])
def deletar(id):
    if 'usuario_id' not in session:
        return redirect('/login')

    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute("SELECT caminho_pdf FROM livros WHERE id = %s", (id,))
    livro = cursor.fetchone()

    if livro:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], livro[0]))

    cursor.execute("DELETE FROM livros WHERE id = %s", (id,))
    conn.commit()
    conn.close()

    return redirect('/')


@app.route('/livro/<int:id>')
def ler_pdf(id):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT caminho_pdf FROM livros WHERE id = %s", (id,))
    livro = cursor.fetchone()
    conn.close()

    if livro:
        caminho_pdf = livro[0]
        return send_from_directory(app.config['UPLOAD_FOLDER'], caminho_pdf)
    else:
        return "Livro não encontrado", 404


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']

        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE username = %s AND senha = %s", (username, senha))
        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            session['usuario_id'] = usuario[0]
            session['username'] = usuario[1]
            return redirect('/')
        else:
            return render_template('login.html', erro="Usuário ou senha inválidos", login_ativo=True, formulario_titulo="Login")

    return render_template('login.html', login_ativo=True, formulario_titulo="Login")


@app.route('/login/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        senha = request.form['senha']

        # Verifica se o usuário já existe
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
        usuario_existente = cursor.fetchone()

        if usuario_existente:
            return render_template('login.html', erro="Nome de usuário já existe.", login_ativo=False, formulario_titulo="Registrar")

        # Adiciona o novo usuário no banco de dados
        cursor.execute("""
            INSERT INTO usuarios (username, email, senha) 
            VALUES (%s, %s, %s)
        """, (username, email, senha))
        
        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('login.html', login_ativo=False, formulario_titulo="Registrar")


# Rota de logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
