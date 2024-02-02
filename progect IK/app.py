from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session, g    #pip install Flask
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import cv2                                                                         #pip install opencv-python
from flask_cors import CORS                                                        #pip install Flask-Cors
import pandas as pd                                                                #pip install pandas  and  pip install openpyxl
import time
from datetime import datetime
import qrcode                                                                      #pip install qrcode  and  pip install pillow
from io import BytesIO
import base64
import sqlite3
import xlsxwriter                                                                   #pip install xlsxwriter  

# pip install -r requirements.txt

app = Flask(__name__)
app.secret_key = '123456789'
cors = CORS(app, resources={r"/uploader": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Подключение к базе данных SQLite
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Создание таблицы users, если она не существует
cursor.execute("CREATE TABLE IF NOT EXISTS users (Login TEXT, Name TEXT, Surname TEXT, Password TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS test (ФИО TEXT, Время TEXT)")


# Проверка, существует ли пользователь "admin" в таблице users
cursor.execute("SELECT * FROM users WHERE Login=?", ('admin',))
user = cursor.fetchone()
if user is None:
    # Добавление пользователя "admin" в таблицу users
    cursor.execute("INSERT INTO users (Login, Name, Surname, Password) VALUES (?, ?, ?, ?)", ('admin', 'admin', 'admin', 'qwerty'))
    conn.commit()



DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

    def get_id(self):
        return str(self.id)
    
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False
    

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

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

        flash('Вы успешно зарегистрировались!')
        return render_template('success.html')
    else:
        return render_template('register.html')
    
    
@app.route('/success', methods=['GET', 'POST'])
def success():
    if request.method == 'POST':
            login = request.form.get('login')
            password = request.form.get('password')
            session['login'] = login
            print('Take ', login, password)

            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE Login=?", (login,))
            user = cursor.fetchone()

            if login == 'admin' and password == 'qwerty':
                flash('Вы успешно вошли как администратор!')
                print('admin is coming!')
                return render_template('admin.html')
            
            elif user is not None and user[3] == password:
                user_object = User(login)
                flash('Вы успешно вошли!')
                login_user(user_object)
                conn.close()
                return redirect(url_for('dashboard'))

            error = 'Неверное имя пользователя или пароль'
            conn.close()
            flash(error)
            return render_template('success.html', error=error)

    return render_template('success.html')


@app.route('/dashboard')
@login_required
def dashboard():
    login = current_user.get_id()
    print(login)
    user_data = login

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE Login=?", (login,))
    user = cursor.fetchone()
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

    return render_template('user.html', user_data=user_data, login = current_user.id)



    
@app.route('/admin', methods = ['GET', 'POST'])
@login_required
def admin(): 
    print('admin is coming!')
    return render_template('admin.html')


@app.route('/admin/download_db_test', methods = ['GET', 'POST'])
@login_required
def admin_download_test():
     
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test")
    test_results = cursor.fetchall()

    test_df = pd.DataFrame(test_results, columns=['ФИО', 'Время'])

    writer = pd.ExcelWriter('output_test.xlsx', engine='xlsxwriter')
    test_df.to_excel(writer, sheet_name='Test', index=False)
    writer.close()

    db_file_path = 'output_test.xlsx' 
    return send_file(db_file_path, as_attachment=True)

@app.route('/admin/download_db_users', methods = ['GET', 'POST'])
@login_required
def admin_download_users():
     
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users_results = cursor.fetchall()


    users_df = pd.DataFrame(users_results, columns=['Login', 'Name', 'Surname', 'Password'])

    writer = pd.ExcelWriter('output_users.xlsx', engine='xlsxwriter')
    users_df.to_excel(writer, sheet_name='Users', index=False)
    writer.close()

    db_file_path = 'output_users.xlsx' 
    return send_file(db_file_path, as_attachment=True)


@app.route('/cam', methods = ['GET', 'POST'])
def cam():
    global result
    if request.method == 'POST':
        data = request.form.get('data')

        ep_time = time.time()
        time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ep_time))
        time_for_qr_test = datetime.now().strftime('%H:%M')


        login, time_qr = data.split()
        print(login, time_qr)


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
                    flash(result)
                    result = 'Все отлично, проходите'
                    server_response = "yes"
                    # return render_template('cam.html', result=result, response = server_response)
                    return "yes"
                else:
                    print('//////////////////////////////////////////////////////////////////////////////////////////               NONONONONONONONONO')
                    result = 'Ошибка... Вас нет в базе данных'
                    server_response = "no"
                    print(server_response)
                    flash(result)
                    # return render_template('cam.html', result=result, response = server_response)
                    return "no"
                    



    return render_template('cam.html', result=result)





@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('success'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

# камера работает на http://127.0.0.1:5000/cam, для телефона нужно заходить по "Адаптер беспроводной локальной сети Беспроводная сеть" IPv4-адрес компа, команда ipconfig в cmd

# if __name__ == "__main__":
#     app.run(debug=True)
