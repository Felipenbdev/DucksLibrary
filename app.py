from flask import Flask, render_template, request, redirect, send_from_directory
import pymysql
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'static/livros'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def connect_to_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="1234567",
        database="biblioteca",
        cursorclass=pymysql.cursors.Cursor  # opcional, mas mantém o cursor padrão
    )


@app.route('/')
def index():
    print("iniciando...")
    conn = connect_to_db()
    print("Conectado")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM livros")
    livros = cursor.fetchall()
    conn.close()
    return render_template('index.html', livros=livros)


@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
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


if __name__ == '__main__':
    app.run(debug=True)
