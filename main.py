from flask import Flask, render_template, redirect, request, session, url_for
from flask_login import LoginManager, login_user, login_required, logout_user
from loginform import LoginForm
import pandas as pd
import matplotlib.pyplot as plt
import csv
import os
from data import db_session
from data.users import User
from data.dataset import Dataset
from forms.user import LoginForm, RegisterForm
import datetime
from werkzeug.utils import secure_filename


app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    hours=1)
app.config['UPLOAD_FOLDER'] = 'user_files'
login_manager = LoginManager()
login_manager.init_app(app)
regist = False

df = pd.read_csv('test1.csv', delimiter=";", quotechar='"')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/preview")
@app.route("/")
def training_prof():
    if 'preview' not in session:

        df['Дата'] = pd.to_datetime(df['Дата'])

        category_sum = df.groupby('Категория')['Сумма'].sum()

        # plt.figure(figsize=(6, 6))
        category_sum.plot(kind='pie', autopct='%1.1f%%')
        plt.title('Расходы по категориям')
        plt.subplots_adjust(bottom=0.15)

        plt.savefig('static\circular.png')

        plt.close()

        # plt.figure(figsize=(5, 6))
        category_sum.plot(kind='bar')
        plt.xlabel('Категория')
        plt.ylabel('Сумма')
        plt.title('Расходы по категориям')

        plt.subplots_adjust(bottom=0.22)

        plt.savefig('static\diagram.png')
        plt.close()

        session['preview'] = True

    return render_template('analitica.html', title='Предпросмотр', data=df.values.tolist())


@app.route("/analitica", methods=['GET', 'POST'])
def file_selection():
    if 'registered' in session:
        db_sess = db_session.create_session()
        files = db_sess.query(Dataset).filter(Dataset.user_id == session.get('user_id')).all()
        return render_template('analitica.html', title='Аналитика',
                               files=files, data=df.values.tolist())
    return redirect('/register')


@app.route("/analitica/<file>", methods=['GET', 'POST'])
def analitica(file=None):
    if 'registered' in session:
        db_sess = db_session.create_session()
        files = db_sess.query(Dataset).filter(Dataset.user_id == session.get('user_id')).all()
        if file in [fil.title for fil in files]:
            return render_template('analitica.html',
                                   title='Аналитика', files=files, data=df.values.tolist())
    return redirect('/register')


@app.route("/profile", methods=['GET', 'POST'])
def profile():
    if 'registered' in session:
        db_sess = db_session.create_session()
        if request.method == 'POST':
            file = request.files['file']
            if file.filename != '':
                username = session['user']
                user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
                os.makedirs(user_folder, exist_ok=True)
                filename = secure_filename(file.filename)
                file.save(os.path.join(user_folder, filename))

                dataset = Dataset(
                    title=file.filename.replace(' ', '_'),
                    user_id=session.get('user_id')

                )
                db_sess.add(dataset)
                db_sess.commit()
        files = db_sess.query(Dataset).filter(Dataset.user_id == session.get('user_id')).all()
        return render_template('profile.html', title='Профиль', files=files)
    return redirect('/register')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/analitica')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            session['registered'] = True
            session['user'] = user.name
            session['user_id'] = user.id
            return redirect("/profile")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect("/")


if __name__ == '__main__':
    db_session.global_init("db/blogs.db")
    app.run(port=8080, host='127.0.0.3')
