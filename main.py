import os
import time
from typing import Text
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, current_user, logout_user
from flask_socketio import SocketIO, join_room, leave_room, send
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from models import User
from form import RegistrationForm, LoginForm
from passlib.hash import pbkdf2_sha256

# Configure application
app = Flask(__name__)
app.secret_key = 'SECRET KEY'

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:HaiPhong3107@localhost:3306/edcs'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

# Initialize login manager
login = LoginManager(app)
login.init_app(app)


@login.user_loader
def load_user(id_user):
    return User.query.get(int(id_user))


socketio = SocketIO(app, manage_session=False)
ROOMS = ["lounge", "news", "games", "coding"]

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        registration_form = RegistrationForm()
        if registration_form.validate_on_submit():
            username = registration_form.username.data
            password = registration_form.password.data
            hashed_password = pbkdf2_sha256.hash(password)

            new_user = User(username, hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Successfully! Please go back to login.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html', form=registration_form)
    except Exception as e:
        return '<h1>' + str(e) + '</h1>'


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()

    if login_form.validate_on_submit():
        user_object = User.query.filter_by(username=login_form.username.data).first()
        print(login_form.username.data)
        login_user(user_object)
        return redirect(url_for('exchange_message'))

    return render_template('login.html', form=login_form)


@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    flash('Logout Successfully!', 'success')
    return redirect(url_for('login'))


@app.route('/exchange_message', methods=['GET', 'POST'])
def exchange_message():
    if not current_user.is_authenticated:
        flash('Please Login!', 'danger')
        return redirect(url_for('login'))
    return render_template('exchange_message.html', username=current_user.username)


@app.route('/search', methods=['GET', 'POST'])
def search():
    name_search = request.form.get('text')
    users = User.query.filter(User.username.like('%' + name_search + '%')).all()
    return jsonify([user.serialize() for user in users])


@socketio.on('incoming-message')
def on_message(data):
    message = data['message']
    username = data['username']
    room = data['room']
    timestamp = time.strftime('%b-%d %I:%M%p', time.localtime())
    send({'username': username, 'message': message, 'timestamp': timestamp}, room=room)


@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send({'message': username + ' has joined ' + room + ' room.'}, room=room)


@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send({'message': username + ' has left the room.'}, room=room)


if __name__ == "__main__":
    app.run(debug=True)
