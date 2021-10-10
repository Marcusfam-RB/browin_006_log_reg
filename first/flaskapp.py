import datetime
import os
import sqlite3

from flask import Flask, render_template, url_for, request, flash, get_flashed_messages, g, abort, redirect

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from flask_database import FlaskDataBase
from user_login import UserLogin
from password import password_check

DATABASE = 'flaskapp.db'
DEBUG = True
SECRET_KEY = 'gheghgj3qhgt4q$#^#$he'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flaskapp.db')))

login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    fdb = FlaskDataBase(get_db())
    print("load_user")
    return UserLogin().from_db(user_id, fdb)


def create_db():
    """Creates new database from sql file."""
    db = connect_db()
    with app.open_resource('db_schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


def connect_db():
    """Returns connention to apps database."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


url_menu_items = {
    'index': 'Главная',
    'second': 'Вторая страница'
}


@app.route('/')
def index():
    fdb = FlaskDataBase(get_db())
    return render_template(
        'index.html',
        menu_url=fdb.get_menu(),
        posts=fdb.get_posts()
    )


@app.route('/page2')
@login_required
def second():
    fdb = FlaskDataBase(get_db())

    print(url_for('second'))
    print(url_for('index'))

    return render_template(
        'second.html',
        phone='+79172345678',
        email='myemail@gmail.com',
        current_date=datetime.date.today().strftime('%d.%m.%Y'),
        menu_url=fdb.get_menu()
    )


# int, float, path
@app.route('/profile')
@login_required
def profile():
    fdb = FlaskDataBase(get_db())
    return render_template(
        'profile.html',
        menu_url=fdb.get_menu()
    ) + f"""<p>Приветствую, номер {current_user.get_id()}!
               <p><a href="{url_for('logout')}"> Выход </a>"""


@app.route('/add_post', methods=["GET", "POST"])
@login_required
def add_post():
    fdb = FlaskDataBase(get_db())

    if request.method == "POST":
        name = request.form["name"]
        post_content = request.form["post"]
        if len(name) > 5 and len(post_content) > 10:
            res = fdb.add_post(name, post_content)
            if not res:
                flash('Post were not added. Unexpected error', category='error')
            else:
                flash('Success!', category='success')
        else:
            flash('Post name or content too small', category='error')

    return render_template('add_post.html', menu_url=fdb.get_menu())


@app.route('/post/<int:post_id>')
@login_required
def post_content(post_id):
    fdb = FlaskDataBase(get_db())
    title, content = fdb.get_post_content(post_id)
    if not title:
        abort(404)
    return render_template('post.html', menu_url=fdb.get_menu(), title=title, content=content)


@app.route('/login', methods=['POST', 'GET'])
def login():
    fdb = FlaskDataBase(get_db())
    if request.method == 'GET':
        return render_template('login.html', menu_url=fdb.get_menu())
    elif request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email:
            flash('Email не указан!', category='unfilled_error')
        else:
            if '@' not in email or '.' not in email:
                flash('Некорректный email!', category='validation_error')
            else:
                if not password:
                    flash('Пароль не указан!', category='unfilled_error')
                else:
                    user = fdb.get_user_by_email(email)
                    print(user)
                    if user and check_password_hash(user['password'], password):
                        userlogin = UserLogin().create(user)
                        login_user(userlogin)
                        return redirect(url_for('profile'))
                    flash("Неверный логин или пароль", "validation_error")

        print(request)
        print(get_flashed_messages(True))
        return render_template('login.html', menu_url=fdb.get_menu())
    else:
        raise Exception(f'Method {request.method} not allowed')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из ккаунта", category="operation_success")
    return redirect(url_for('login'))


@app.route("/register", methods=['POST', 'GET'])
def register():
    fdb = FlaskDataBase(get_db())
    if request.method == 'GET':
        return render_template('register.html', menu_url=fdb.get_menu())
    elif request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('repeat')
        if not email:
            flash('Email не указан!', category='unfilled_error')
        else:
            if '@' not in email or '.' not in email:
                flash('Некорректный email!', category='validation_error')
            else:
                if not password or not password2:
                    flash('Пароль не указан!', category='unfilled_error')
                else:
                    if password != password2:
                        flash('Пароли не совпадают!', category='validation_error')
                    else:
                        if password_check(password)['password_ok'] is False:
                            flash('Пароль слишком слабый', category='password_error')
                        else:
                            hash = generate_password_hash(password)
                            user = fdb.add_user(name, email, hash)
                            print(user)
                            if user:
                                flash("Регистрация прошла успешно", "operation_success")
                            else:
                                flash("пользователь с таким email уже существует", "error")

        print(request)
        print(get_flashed_messages(True))
        return render_template('register.html', menu_url=fdb.get_menu())
    else:
        raise Exception(f'Method {request.method} not allowed')


@app.errorhandler(404)
def page_not_found(error):
    return "<h1>Ooooops! This post does not exist!</h1>"


@app.teardown_appcontext
def close_db(error):
    """Close database connection if it exists."""
    if hasattr(g, 'link_db'):
        g.link_db.close()


if __name__ == '__main__':
    app.run(debug=True)
