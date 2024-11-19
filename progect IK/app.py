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








#настройка сервера
app = Flask(__name__)
app.secret_key = '123456789'
cors = CORS(app, resources={r"/uploader": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['TEMPLATES_AUTO_RELOAD'] = True

#настройка БД
conn = sqlite3.connect('database.db')
cursor = conn.cursor()


cursor.execute("CREATE TABLE IF NOT EXISTS ppls (School_num INTEGER, Sity TEXT, Indx INTEGER, Login TEXT, Password TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS schools (Login TEXT, Num INTEGER, Sity TEXT, Inx INTEGER,  Password TEXT)")




DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

#настройка входа и выхода личного кабинета
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

#главная страница
@app.route('/')
def test():
    return """
        <h1>Добро пожаловать на главную страницу!</h1>
        <button onclick="location.href='/register'">Регистрация</button>
        <button onclick="location.href='/success'">Вход</button>
        """

#страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():

#получение данных с веб-страницы
    if request.method == 'POST':
        login = request.form['login']
        name = request.form['name']
        password = request.form['password']
        surname = request.form['surname']
        ppl_class = request.form['ppl_class']
        simv = request.form['simv']
        sch = request.form['sch']
        idx = request.form['idx']
        sity = request.form['sity']

#запись в БД
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("INSERT INTO ppls (School_num, Sity, Indx, Login, Password) VALUES (?, ?, ?, ?, ?)", (sch, sity, idx, login, password))
        cursor.execute(f"INSERT INTO users{idx}__{sch} (Login, ppl_class, simv, Name, Surname, Password) VALUES (?, ?, ?, ?, ?, ?)", (login, ppl_class, simv, name, surname, password))
        conn.commit()
        conn.close()

        flash('Вы успешно зарегистрировались!')
        return render_template('success.html')
    else:
        return render_template('register.html')
    
#страница входа
@app.route('/success', methods=['GET', 'POST'])
def success():
    if request.method == 'POST':
            
#получение данных с веб-страницы
            login = request.form.get('login')
            password = request.form.get('password')
            
            session['login'] = login
            print('Take ', login, password)
            
#получение данных с БД
            conn = sqlite3.connect('database.db', check_same_thread=False)
            cursor = conn.cursor()

            
            cursor.execute(f"SELECT * FROM schools WHERE Login=?", (login,))
            admins_logs = cursor.fetchone()
            print(admins_logs)

            cursor.execute(f"SELECT * FROM ppls WHERE Login=?", (login,))
            user = cursor.fetchone()
            print(user)


#проверка данных, которые ввел пользователь

            if login == "admin" and password == "qwerty":
                return redirect(url_for('admin_sch'))
            

            elif user is not None and user[4] == password:
                user_object = User(login)
                flash('Вы успешно вошли!')
                login_user(user_object)

                return redirect(url_for('dashboard'))
            
            
            else:
                if admins_logs is not None and login == admins_logs[0] and password == admins_logs[4]:
                    flash('Вы успешно вошли как администратор!')
                    admin_object = User(login)
                    login_user(admin_object)
                    print('admin is coming!')

                    return redirect(url_for('admin'))

            

#вывод ошибки
            error = 'Неверное имя пользователя или пароль'
            conn.close()
            flash(error)
            return render_template('success.html', error=error)

    return render_template('success.html')

#страница личного кибанета
@app.route('/dashboard')
# @login_required
def dashboard():

    login = current_user.get_id()
    print(login)
    print('#######################', session)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM ppls WHERE Login=?", (login,))
    sch_data_user = cursor.fetchone()
    print(sch_data_user)

    cursor.execute(f"SELECT * FROM users{sch_data_user[2]}__{sch_data_user[0]} WHERE Login=?", (login,))
    user_data = cursor.fetchone()
    name, surname = user_data[3], user_data[4]

#обработка данных и генерация QR-кода
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(f"{login} {datetime.now().strftime('%H:%M')}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    # Преобразование изображения в строку в формате base64
    buffered = BytesIO()
    qr_img.save(buffered, format="PNG")
    qr_img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
    user_data = {'name': name, 'surname': surname, 'qr_code': qr_img_str, 'login': login}

    return render_template('user.html', user_data=user_data, login = current_user.id)



#панель управление школы
@app.route('/admin', methods = ['GET', 'POST'])
# @login_required
def admin(): 
    print('#######################', session)
    login = current_user.get_id()
    print(login)
    # login = login

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM schools WHERE Login=?", (login,))
    adm_data = cursor.fetchone()
    print(adm_data)
    user_data = [adm_data[1], adm_data[2]]

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users{adm_data[3]}__{adm_data[1]}")
    database_data = cursor.fetchall()
    print(database_data)

    print('admin is coming!')
    return render_template('admin.html', user_data = user_data, database_data = database_data)


#панель управления самого сервиса
@app.route('/admin-sch', methods = ['GET', 'POST'])
# @login_required
def admin_sch(): 

    if request.method == 'POST':
        login = request.form['login']
        num = request.form['num']
        password = request.form['password']
        sity = request.form['sity']
        inx = request.form['inx']



        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute(f"INSERT INTO schools (Login, Num, Sity, Inx,  Password) VALUES (?, ?, ?, ?, ?)", (login, num, sity, inx, password))
        cursor.execute(f"CREATE TABLE users{inx}__{num} (Login TEXT, ppl_class INTEGER, simv TEXT, Name TEXT, Surname TEXT, Password TEXT)")
        cursor.execute(f"CREATE TABLE test{inx}__{num} (ФИО TEXT, Класс TEXT, Время TEXT)")

        # cursor.execute("INSERT INTO admins (School_num, Indx, Sity, Login, Password) VALUES (?, ?, ?, ?, ?)", (num, inx, sity, login, password))

        conn.commit()
        conn.close()


        return render_template('admin_sch.html')
    else:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM schools')
        database_data = cursor.fetchall()
        
        return render_template('admin_sch.html', database_data = database_data)

#преобразование SQL БД в Excel
@app.route('/admin/download_db_test', methods = ['GET', 'POST'])
def admin_download_test():
    login = current_user.get_id()
    print(login)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM schools WHERE Login=?", (login,))
    adm_data = cursor.fetchone()
    print(adm_data)
    num, indx = adm_data[1], adm_data[3]
     
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM test{indx}__{num}")
    test_results = cursor.fetchall()

    test_df = pd.DataFrame(test_results, columns=['ФИО', "Класс", 'Время'])

    writer = pd.ExcelWriter('output_test.xlsx', engine='xlsxwriter')
    test_df.to_excel(writer, sheet_name='Test', index=False)
    writer.close()

    db_file_path = 'output_test.xlsx' 
    return send_file(db_file_path, as_attachment=True)

@app.route('/admin/download_db_users', methods = ['GET', 'POST'])
def admin_download_users():
    login = current_user.get_id()
    print(login)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT * FROM schools WHERE Login=?", (login,))
    adm_data = cursor.fetchone()
    print(adm_data)
    num, indx = adm_data[1], adm_data[3]
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users{indx}__{num}")
    users_results = cursor.fetchall()
    print(users_results)

    users_df = pd.DataFrame(users_results, columns=['Логин', 'Класс', 'Буква', 'Имя', 'Фамилия', 'Пароль'])

    writer = pd.ExcelWriter('output_users.xlsx', engine='xlsxwriter')
    users_df.to_excel(writer, sheet_name='Users', index=False)
    writer.close()

    db_file_path = f'output_users{indx}__{num}.xlsx' 
    return send_file(db_file_path, as_attachment=True)

#страница с камерой
@app.route('/cam', methods = ['GET', 'POST'])
@login_required
def cam():
    login = current_user.get_id()
    print(login)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM schools WHERE Login=?", (login,))
    adm_data = cursor.fetchone()
    print(adm_data)
    user_data = [adm_data[1], adm_data[2]]

    global result
    if request.method == 'POST':
        data = request.form.get('data')

        ep_time = time.time()
        time_now = time.strftime('%d-%m-%Y, %H:%M:%S', time.localtime(ep_time))
        time_for_qr_test = datetime.now().strftime('%H:%M')


        login, time_qr = data.split()
        print(login, time_qr)


        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM users{adm_data[3]}__{adm_data[1]} WHERE Login=?", (login,))
        user = cursor.fetchone()

#обработка данных сервером, которые получены с помощью камеры
        if user is not None:
                if user[0] == login and time_qr == time_for_qr_test:
                    print("Ok!")
                    name_sql = user[3] + ' ' + user[4]
                    ppl_class = str(user[1]) + user[2]
                    print('SQL      ',name_sql, ppl_class)

                    cursor.execute(f"INSERT INTO test{adm_data[3]}__{adm_data[1]} (ФИО, Класс, Время) VALUES (?, ?, ?)", (name_sql, ppl_class, time_now))
                    conn.commit()

                    conn.close()
                    flash(result)
                    result = 'Все отлично, проходите'
                    server_response = "yes"
                    return "yes"
                else:
                    print('//////////////////////////////////////////////////////////////////////////////////////////               NONONONONONONONONO')
                    result = 'Ошибка... Вас нет в базе данных'
                    server_response = "no"
                    print(server_response)
                    flash(result)
                    return "no"
                    



    return render_template('cam.html', result=result, user_data = user_data)




#обработка кнопки выхода
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('success'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

# камера работает на http://127.0.0.1:5000/, для телефона нужно заходить IPv4-адрес компа

