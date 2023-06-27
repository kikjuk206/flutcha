from flask import Flask, render_template, request, redirect, url_for    #pip install Flask
import cv2                                                              #pip install opencv-python
from flask_cors import CORS                                             #pip install Flask-Cors
import pandas as pd                                                     #pip install pandas  and  pip install openpyxl
import time
from datetime import datetime
import qrcode                                                           #pip install qrcode  and  pip install pillow
from io import BytesIO
import base64
import sqlite3






app = Flask(__name__)
cors = CORS(app, resources={r"/uploader": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['TEMPLATES_AUTO_RELOAD'] = True

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (Login TEXT, Name TEXT, Surname TEXT, Password TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS test (ФИО TEXT, Время TEXT)")

result = ''
error = ''


@app.route('/')
def test():
    return """
        <h1>Добро пожаловать на главную страницу!</h1>
        <button onclick="location.href='/register'">Регистрация</button>
        <button onclick="location.href='/success'">Вход</button>
        <button onclick="location.href='/cam'">Камера</button>
        """


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form['login']
        name = request.form['name']
        password = request.form['password']
        surname = request.form['surname']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()


        cursor.execute("INSERT INTO users (Login, Name, Surname, Password) VALUES (?, ?, ?, ?)", (login, name, surname, password))
        conn.commit()
        conn.close()


        return render_template('success.html')
    else:
        return render_template('register.html')
    
    
@app.route('/success', methods=['GET', 'POST'])
def success():

    global error

    login = request.form.get('login')
    password = request.form.get('password')

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE Login = ? AND Password = ?", (login, password))
    user = cursor.fetchone()

    if user is not None:
            if user[0] == login and user[3] == password:
                conn.close()
                print('Ok!')
                return redirect(url_for('profile', login=login))
            else:
                print('error')
                error = 'Неверное имя пользователя или пароль'
                return render_template('success.html', error=error)
            
    return render_template( 'success.html', error=error)


    

@app.route('/profile/<login>')
def profile(login):


    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE Login=?", (login,))
    user = cursor.fetchone()

    if user is not None:
            if user[0] == login:
                print("Ok!")
                conn.close()
                user_data = login
                name = user[1]

                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(f"{user_data} {datetime.now().strftime('%H:%M')}")
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                # Преобразование изображения в строку в формате base64
                buffered = BytesIO()
                qr_img.save(buffered, format="PNG")
                qr_img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
                user_data = {'name': name, 'qr_code': qr_img_str, 'login': login}
                return render_template('user.html', user_data=user_data)
    
            else:
                error = 'Пользователь не найден'
                return render_template('success.html', error=error)

    

    



@app.route('/cam', methods = ['GET', 'POST'])
def cam():
    global result
    if request.method == 'POST':
        file = request.files.get('file')
        print(f'Got file: {request.files}')

        file.save('./photo/original.png')

    
        img = cv2.imread('photo/original.png')
        detector = cv2.QRCodeDetector()
        data, bbox, temp = detector.detectAndDecode(img)
        print(data)

        ep_time = time.time()
        time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ep_time))
        time_for_qr_test = datetime.now().strftime('%H:%M')


        login, time_qr = data.split()



        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE Login=?", (login,))
        user = cursor.fetchone()


        if user is not None:
                if user[0] == login and time_qr == time_for_qr_test:
                    print("Ok!")
                    name_sql = user[1] + ' ' + user[2]
                    print('SQL',name_sql)

                    cursor.execute("INSERT INTO test (ФИО, Время) VALUES (?, ?)", (name_sql, time_now))
                    conn.commit()

                    conn.close()
                    result = 'Все отлично, проходите'
                    return render_template('cam.html', result=result)
                else:
                    print('//////////////////////////////////////////////////////////////////////////////////////////               NONONONONONONONONO')
                    result = 'Ошибка... Вас нет в базе данных'
                    return render_template('cam.html', result=result)
                    



    return render_template('cam.html', result=result)








if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

# камера работает на http://127.0.0.1:5000/cam, нужно заходить по "Адаптер беспроводной локальной сети Беспроводная сеть" IPv4-адрес компа, команда ipconfig в cmd

# if __name__ == "__main__":
#     app.run(debug=True)
