from operator import and_, or_
import os
import re
import time
from typing import Text
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, current_user, logout_user
from flask_socketio import SocketIO, join_room, leave_room, rooms, send
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import form
from werkzeug import debug
from models import User, Conversation, Message, BlockingUser, ConnectedUser
from form import RegistrationForm, LoginForm, SearchForm
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
ROOMS = []
BLK_STATUS = []
BLK_USERS = []

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
    search_form = SearchForm()
    if not current_user.is_authenticated:
        flash('Please Login!', 'danger')
        return redirect(url_for('login'))
    
    connected_user = ConnectedUser.query.filter(ConnectedUser.user1_id == (current_user.id)).all()
    blocking_user = BlockingUser.query.filter(BlockingUser.user_id == current_user.id).all()
    
    for user in blocking_user:
        user_object = User.query.filter(User.id == user.blocked_user_id).first()
        BLK_USERS.append(user_object)
    
    for user in connected_user:
        user_object = User.query.filter(User.id == user.user2_id).first()
        ROOMS.append(user_object)
        if user_object in BLK_USERS:
            BLK_STATUS.append("Un-Block")
        else:
            BLK_STATUS.append("Block")
    return render_template('exchange_message.html', form = search_form, 
                            username=current_user.username, rooms=ROOMS, status=BLK_STATUS, zip=zip)


@app.route('/search', methods=['POST'])
def search():
    search_form = SearchForm()
    if search_form.validate_on_submit:
        users = User.query.filter(User.username.like('%' + search_form.username.data + '%')).all()
        return render_template('exchange_message.html', form = search_form,
                                username=current_user.username, rooms=ROOMS, list_users=users)


@app.route('/connect_user', methods=['POST'])
def connect_user():
    friend_name = request.form.get("name")
    friend_id = request.form.get("id")
    print(friend_name, friend_id)
    test = ConnectedUser.query.filter(
        or_(
            and_(ConnectedUser.user1_id == current_user.id, ConnectedUser.user2_id == friend_id),
            and_(ConnectedUser.user1_id == friend_id, ConnectedUser.user2_id == current_user.id)
            )).first()

    if test is None:
        new_friend = ConnectedUser(current_user.id, friend_id)
        db.session.add(new_friend)
        db.session.commit()
        user_object = User.query.filter(User.id == friend_id).first()
        ROOMS.append(user_object)
        # search_form = SearchForm()
        # return render_template('exchange_message.html', form = search_form,
        # username=current_user.username, rooms=ROOMS)
        result = {"msg": "Connect to friend successfully!"}
        return jsonify(result)
    else:
        result = {"msg": "The connection is already exist!"}
        return jsonify(result)


@app.route('/block_user', methods = ['POST'])
def block_user():
    friend_id = request.form.get("id")
    action = request.form.get("action")
    print(friend_id, action)
    if action == 'Block':
        new_block = BlockingUser(current_user.id, friend_id)
        db.session.add(new_block)
        db.session.commit()
        result = {"msg": "Block user successfully!"}
    else:
        block = BlockingUser.query.filter(and_(BlockingUser.user_id == current_user.id, 
        BlockingUser.blocked_user_id == friend_id)).first()
        print(block)
        current_session = db.session.object_session(block)
        current_session.delete(block)
        current_session.commit()
        result = {"msg": "Unblock user successfully!"}
    return jsonify(result)


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@socketio.on('message')
def message(data):
    msg = data['msg']
    username = data['username']
    room = data['room']
    timestamp = time.strftime('%b-%d %I:%M%p', time.localtime())
    print(msg)
    send({'username': username, 'msg': msg, 'timestamp': timestamp}, room=room)


@socketio.on('join')
def join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    # print('join room: ', room, 'username: ', username)
    send({'message': username + ' has joined ' + room + ' room.'}, room=room)


@socketio.on('leave')
def leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    # print('leave room: ', room, 'username: ', username)
    send({'message': username + ' has left the room.'}, room=room)


if __name__ == "__main__":
    # socketio.run(app, debug=True)
    app.run(debug=True)
