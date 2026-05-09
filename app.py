from flask import Flask, render_template, request, redirect, session
import tensorflow as tf
import numpy as np
from PIL import Image
import sqlite3
import os
import webbrowser

app = Flask(__name__)
app.secret_key = "secret"

# ---------------- LOAD MODEL ----------------
model = tf.keras.models.load_model('model.h5')

class_names = ['Healthy', 'Disease']

# ---------------- DATABASE ----------------
def init_db():

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # user table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')

    # history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            image TEXT,
            result TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- PREDICT FUNCTION ----------------
def predict_image(img_path):

    img = Image.open(img_path).convert('RGB').resize((224,224))
    img = np.array(img) / 255.0
    img = np.expand_dims(img, axis=0)

    prediction = model.predict(img)

    return class_names[np.argmax(prediction)]

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        c.execute(
            "INSERT INTO users(username,password) VALUES (?,?)",
            (username,password)
        )

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        )

        user = c.fetchone()

        conn.close()

        if user:
            session['user'] = username
            return redirect('/')

        else:
            return "Invalid Username or Password"

    return render_template('login.html')

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect('/login')

# ---------------- MAIN PAGE ----------------
@app.route('/', methods=['GET','POST'])
def index():

    if 'user' not in session:
        return redirect('/login')

    result = None

    if request.method == 'POST':

        file = request.files['file']

        os.makedirs('static', exist_ok=True)

        filename = "uploaded.jpg"

        path = os.path.join('static', filename)

        file.save(path)

        # prediction
        result = predict_image(path)

        # save history
        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        c.execute(
            "INSERT INTO history(username,image,result) VALUES (?,?,?)",
            (session['user'], filename, result)
        )

        conn.commit()
        conn.close()

    return render_template('index.html', result=result)

# ---------------- HISTORY ----------------
@app.route('/history')
def history():

    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    c.execute(
        "SELECT image,result FROM history WHERE username=?",
        (session['user'],)
    )

    data = c.fetchall()

    conn.close()

    return render_template('history.html', data=data)

# ---------------- PROFILE ----------------
@app.route('/profile')
def profile():

    if 'user' not in session:
        return redirect('/login')

    return render_template(
        'profile.html',
        username=session['user']
    )

# ---------------- RUN APP ----------------
if __name__ == "__main__":

    webbrowser.open("http://127.0.0.1:5000/register")

    app.run(debug=True)