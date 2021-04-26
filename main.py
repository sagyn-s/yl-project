# -*- coding: utf-8 -*-
from flask import Flask, render_template, redirect, abort, request, jsonify, make_response, url_for, session
from data.users import User
from data import db_session, jobs_api
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from wtforms import SubmitField, BooleanField, PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from forms.jobs import JobsForm
from data.jobs import Jobs
from forms.user import RegisterForm
from flask_restful import reqparse, abort, Api, Resource
import users_resource
import jobs_resource
from data.works import Works
import requests
from data.chat import Chat

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_session.global_init("db/blogs.db")
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('basic.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('basic.html', title='Авторизация', form=form)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    jobs = db_sess.query(Jobs).all()
    lst = {}
    if current_user.is_authenticated:
        for i in jobs:
            for j in current_user.works:
                if i.id == j.job_id:
                    lst[i.id] = 1
                else:
                    lst[i.id] = 0
    return render_template("ji.html", jobs=jobs, lst=lst)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data or User.name == form.name.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/news',  methods=['GET', 'POST'])
@login_required
def add_news():
    form = JobsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        jobs = Jobs()
        jobs.title = form.title.data
        jobs.team_leader = form.team_leader.data
        jobs.work_size = form.work_size.data
        jobs.collaborators = form.collaborators.data
        jobs.is_finished = form.is_finished.data
        current_user.jobs.append(jobs)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('jobs.html', title='Добавление работы',
                           form=form)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = JobsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        jobs = db_sess.query(Jobs).filter(Jobs.id == id,
                                          (Jobs.user == current_user)|(current_user.id == 1),

                                          ).first()
        if jobs or (jobs and current_user.id == 1):
            jobs.title = form.title.data
            jobs.team_leader = form.team_leader.data
            jobs.work_size = form.work_size.data
            jobs.collaborators = form.collaborators.data
            jobs.is_finished = form.is_finished.data
            jobs.is_finished = form.is_finished.data
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        jobs = db_sess.query(Jobs).filter(Jobs.id == id,
                                          (Jobs.user == current_user)|(current_user.id == 1),
                                          ).first()
        if jobs or (jobs and current_user.id == 1):
            jobs.title = form.title.data
            jobs.team_leader = form.team_leader.data
            jobs.work_size = form.work_size.data
            jobs.collaborators = form.collaborators.data
            jobs.is_finished = form.is_finished.data
            jobs.is_finished = form.is_finished.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('jobs.html',
                           title='Редактирование работы',
                           form=form
                           )


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(Jobs).filter(Jobs.id == id,
                                      (Jobs.user == current_user)|(current_user.id == 1)
                                      ).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/work/<int:id>', methods=['GET', 'POST'])
@login_required
def work(id):
    db_sess = db_session.create_session()
    jobs = db_sess.query(Jobs).filter(Jobs.id == id,
                                      ).first()
    works = Works()
    works.title = jobs.title
    works.team_leader = jobs.team_leader
    works.work_size = jobs.work_size
    works.collaborators = jobs.collaborators
    works.is_finished = jobs.is_finished
    print(f"++++++++++++++++++++++++++++++++{jobs.id}")
    works.job_id = jobs.id
    current_user.works.append(works)
    db_sess.merge(current_user)
    db_sess.commit()
    return redirect('/')


@app.route('/profile/<int:id>')
def profile(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(id)
    return render_template('profile.html', user=user)


@app.route('/chat/<int:id>', methods=['GET', 'POST'])
@login_required
def chat(id):
    if request.method == "GET":
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(id)
        name = user.name
        messages = db_sess.query(Chat).all()
        return render_template('chat.html', name=name, messages=messages)
    elif request.method == "POST":
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(id)
        name = user.name
        chat = Chat()
        chat.message = request.form['message']
        chat.user1_id = id
        current_user.messages.append(chat)
        db_sess.merge(current_user)
        db_sess.commit()
        messages = db_sess.query(Chat).all()
        return render_template('chat.html', name=name, messages=messages)


@app.route('/stop_work/<int:id>')
def stop_work(id):
    db_sess = db_session.create_session()
    work = db_sess.query(Works).filter(Works.job_id == id).first()
    if work:
        db_sess.delete(work)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        return render_template('search.html')
    elif request.method == 'POST':
        name = request.form['name']
        response = requests.get('http://localhost:8080/api/v2/users').json()
        ans = []
        for i in response['users']:
            if not current_user.is_authenticated:
                if name in i['name']:
                    ans.append(i)
            else:
                if name in i['name'] and i['name'] != current_user.name:
                    ans.append(i)
        return render_template('search.html', ans=ans)


@app.route('/searchjobs', methods=['GET', 'POST'])
def searchjobs():
    if request.method == 'GET':
        return render_template('searchjobs.html')
    elif request.method == 'POST':
        name = request.form['name']
        response = requests.get('http://localhost:8080/api/v2/jobs').json()
        ans = []
        for i in response['jobs']:
            if name in i['title']:
                ans.append(i)

        return render_template('searchjobs.html', ans=ans)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': f'{error}'}), 404)


@app.route('/delete_user/<int:id>')
@login_required
def delete_user(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id,
                                      (User.id == current_user.id) | (current_user.id == 1)
                                      ).first()
    jobs = db_sess.query(Jobs).filter(Jobs.user_id == id
                                      ).all()
    works = db_sess.query(Works).filter(Works.user_id == id
                                        ).all()
    messages = db_sess.query(Chat).filter((Chat.user1_id == id) | (Chat.user_id == id)).all()
    if user:
        db_sess.delete(user)
        db_sess.commit()
    else:
        abort(404)
    if jobs:
        for i in jobs:
            db_sess.delete(i)
            db_sess.commit()
    if messages:
        for i in messages:
            db_sess.delete(i)
            db_sess.commit()
    if works:
        for i in works:
            db_sess.delete(i)
            db_sess.commit()
    logout_user()
    return redirect('/')


@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    form = RegisterForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id, (User.id == current_user.id) | (current_user.id == 1)).first()
        if user:
            user.name = form.name.data
            user.email = form.email.data
            user.about = form.about.data

        else:
            abort(404)
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Редактирование пользователя',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == id, (User.id == current_user.id) | (current_user.id == 1)).first()
        if db_sess.query(User).filter(User.email == form.email.data or User.name == form.name.data).first():
            return render_template('register.html', title='Редактирование пользователя',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if user:
            user.name = form.name.data
            user.email = form.email.data
            user.about = form.about.data
            user.set_password(form.password.data)
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('register.html', title='Редактирование пользователя', form=form)


if __name__ == '__main__':
    db_session.global_init("db/blogs.db")
    app.register_blueprint(jobs_api.blueprint)
    api.add_resource(users_resource.UsersListResource, '/api/v2/users')
    api.add_resource(users_resource.UserResource, '/api/v2/users/<int:user_id>')
    api.add_resource(jobs_resource.JobsListResource, '/api/v2/jobs')
    api.add_resource(jobs_resource.JobResource, '/api/v2/jobs/<int:job_id>')
    app.run(port=8080, host='127.0.0.1')
