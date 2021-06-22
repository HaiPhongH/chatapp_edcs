from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password
        }

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user1_id = db.Column(db.Integer, nullable=False)
    user2_id = db.Column(db.Integer, nullable=False)

    def __init__(self, user1_id, user2_id):
        self.user1_id = user1_id
        self.user2_id = user2_id

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    content = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=True)
    conversation_id = db.Column(db.Integer, nullable=False)

    def __init__(self, content, timestamp, conversation_id):
        self.content = content
        self.timestamp = timestamp
        self.conversation_id = conversation_id

class BlockingUser(db.Model):
    __tablename__ = 'blocking_users'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    blocked_user_id = db.Column(db.Integer, nullable=False)

    def __init__(self, user_id, blocked_user_id):
        self.user_id = user_id
        self.blocked_user_id = blocked_user_id

class ConnectedUser(db.Model):
    __tablename__ = 'connected_users'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user1_id = db.Column(db.Integer, nullable=False)
    user2_id = db.Column(db.Integer, nullable=False)

    def __init__(self, user1_id, user2_id):
        self.user1_id = user1_id
        self.user2_id = user2_id
