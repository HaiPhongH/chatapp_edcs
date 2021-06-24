from operator import and_, or_
import os
import re
import time
from typing import Text
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask.globals import session
from flask_login import LoginManager, login_user, current_user, logout_user
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms, send
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import form
from werkzeug import debug
from models import UserGlobal, ChatRoom, BlockList, Message
from form import RegistrationForm, LoginForm, SearchForm
from passlib.hash import pbkdf2_sha256
from datetime import datetime

# Configure application
app = Flask(__name__)
app.secret_key = 'SECRET KEY'

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:HaiPhong3107@localhost:3306/distributed_project'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

# Initialize login manager
login = LoginManager(app)
login.init_app(app)


@login.user_loader
def load_user(id_user):
    return UserGlobal.query.get(int(id_user))


socketio = SocketIO(app, manage_session=False)
STATUSES = {}

def hashpassword(password):
    hash = 0
    if (len(password) == 0): 
        return hash
    for i in range(len(password)):
        chr   = ord(password[i])
        hash  = ((hash << 5) - hash) + chr
        hash |= 0; # Convert to 32bit integer
    return str(hash)

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        registration_form = RegistrationForm()
        if registration_form.validate_on_submit():
            username = registration_form.username.data
            password = registration_form.password.data
            hashed_password = hashpassword(password)

            new_user = UserGlobal(userId=1, name=username, serverId=1, hashpass=hashed_password)
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
        user_object = UserGlobal.query.filter_by(name=login_form.username.data).first()
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
    ROOMS = []
    ROOM_IDS = {}
    BLOCK_STATUSES = []
    BLOCK_USERS = []
    search_form = SearchForm()
    if not current_user.is_authenticated:
        flash('Please Login!', 'danger')
        return redirect(url_for('login'))
    
    all_users = UserGlobal.query.filter().all()
    # connected_user = ChatRoom.query.filter(or_(
    #     ChatRoom.userGlobal1 == current_user.globalId,
    #     ChatRoom.userGlobal2 == current_user.globalId
    # )).all()
    blocking_user = BlockList.query.filter(BlockList.user == current_user.globalId).all()
    
    for user in blocking_user:
        user_object = UserGlobal.query.filter(UserGlobal.globalId == user.blockedUser).first()
        BLOCK_USERS.append(user_object)
    
    
    for user in all_users:
        # user_object = UserGlobal.query.filter(UserGlobal.globalId == user.userGlobal2).first()
        if user.globalId != current_user.globalId:

            ROOMS.append(user)

            test = ChatRoom.query.filter(or_(
                and_(ChatRoom.userGlobal1 == current_user.globalId, ChatRoom.userGlobal2 == user.globalId),
                and_(ChatRoom.userGlobal1 == user.globalId, ChatRoom.userGlobal2 == current_user.globalId)
            )).first()
            
            if test is None:
                new_rom = ChatRoom(current_user.globalId, user.globalId)
                db.session.add(new_rom)
                db.session.commit()
                ROOM_IDS[user.globalId] = new_rom.id
            else:
                ROOM_IDS[user.globalId] = test.id

            if user.globalId not in STATUSES:
                STATUSES[user.globalId] = 'offline'                
        else:
            STATUSES[user.globalId] = 'online'

        if user in BLOCK_USERS:
            BLOCK_STATUSES.append("Un-Block")
        else:
            BLOCK_STATUSES.append("Block")
    
    return render_template('exchange_message.html', form = search_form, 
                            username=current_user.name, id=current_user.globalId, room_ids=ROOM_IDS,
                            rooms=ROOMS, block_statuses=BLOCK_STATUSES, statuses=STATUSES, zip=zip)


# @app.route('/search', methods=['POST'])
# def search():
#     search_form = SearchForm()
#     if search_form.validate_on_submit:
#         search_users = UserGlobal.query.filter(UserGlobal.name.like('%' + search_form.username.data + '%')).all()
#         # return redirect(url_for('.exchange_message', search_users=search_users))
#         return render_template('exchange_message.html', form = search_form,
#                                 username=current_user.name, search_users=search_users, 
#                                 rooms=ROOMS, blk_status=BLK_STATUS, zip=zip)


# @app.route('/connect_user', methods=['POST'])
# def connect_user():
#     friend_name = request.form.get("name")
#     friend_id = request.form.get("id")
#     print(friend_name, friend_id)
#     test = ChatRoom.query.filter(
#         or_(
#             and_(ChatRoom.userGlobal1 == current_user.globalId, ChatRoom.userGlobal2 == friend_id),
#             and_(ChatRoom.userGlobal1 == friend_id, ChatRoom.userGlobal2 == current_user.globalId)
#             )).first()

    # if test is None:
    #     new_friend = ChatRoom(current_user.globalId, friend_id)
    #     db.session.add(new_friend)
    #     db.session.commit()
    #     user_object = UserGlobal.query.filter(UserGlobal.globalId == friend_id).first()
    #     ROOMS.append(user_object)
    #     # search_form = SearchForm()
    #     # return render_template('exchange_message.html', form = search_form,
    #     # username=current_user.username, rooms=ROOMS)
    #     result = {"msg": "Connect to friend successfully!"}
    #     return jsonify(result)
    # else:
    #     result = {"msg": "The connection is already exist!"}
    #     return jsonify(result)
    


@app.route('/block_user', methods = ['POST'])
def block_user():
    friend_id = request.form.get("id")
    friend_id = int(friend_id.replace('block_user_', ''))
    action = request.form.get("action")
    print(friend_id, action)
    if action == 'Block':
        new_block = BlockList(current_user.globalId, friend_id, datetime.now())
        db.session.add(new_block)
        db.session.commit()
        result = {"msg": "Block user successfully!"}
    else:
        block = BlockList.query.filter(and_(BlockList.user == current_user.globalId, 
        BlockList.blockedUser == friend_id)).first()
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

@socketio.on('online')
def online(data):
    print(data)
    emit('status_change', {'id': data['id'], 'username': data['username'], 'status': 'online'}, broadcast=True)


@socketio.on('offline')
def offline(data):
    print(data)
    emit('status_change', {'id': data['id'], 'username': data['username'], 'status': 'offline'}, broadcast=True)

@socketio.on('block_sending')
def block_sending(data):
    print(data)
    emit('disable_button', {'userid': data['userid'], 'blocked_id': data['blocked_id'], 'action': data['action']}, broadcast=True)

@socketio.on('message')
def message(data):
    msg = data['msg']
    username = data['username']
    room = data['room']
    room_id = int(room.replace('choose_room_', ''))
    timestamp = datetime.now()
    print(msg, username, room, timestamp)

    new_msg = Message(roomId=room_id, userGlobal=current_user.globalId, content=msg, timeStamp=timestamp)
    db.session.add(new_msg)
    db.session.commit()
    send({'username': username, 'msg': msg, 'time_stamp': str(timestamp)}, room=room)


@socketio.on('join')
def join(data):
    username = data['username']
    room = data['room']
    roomName = data['roomName']
    join_room(room)
    print('join room: ', room, 'username: ', username)
    send({'msg': username + ' has joined the room with ' + roomName + '.'}, room=room)


@socketio.on('leave')
def leave(data):
    username = data['username']
    room = data['room']
    roomName = data['roomName']
    leave_room(room)
    print('leave room: ', room, 'username: ', username)
    send({'msg': username + ' has left the room with ' + roomName + '.'}, room=room)


if __name__ == "__main__":
    # socketio.run(app, debug=True)
    app.run(debug=True)
