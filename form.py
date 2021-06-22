from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, EqualTo, ValidationError
from passlib.hash import pbkdf2_sha256
from models import User


def validate_profile(form, field):
    password = field.data
    username = form.username.data

    user_data = User.query.filter_by(username=username).first()
    if user_data is None:
        raise ValidationError("Name or password is incorrect!")
    elif not pbkdf2_sha256.verify(password, user_data.password):
        raise ValidationError("Name or password is incorrect!")


class RegistrationForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(message="user Name Required"),
                                                         Length(min=1, max=45,
                                                                message="The length must be between 5 and 45 characters")])

    password = PasswordField('password', validators=[InputRequired(message="Password Required"),
                                                     Length(min=1, max=45,
                                                            message="The length must be between 5 and 45 characters")])

    confirm_password = PasswordField('confirm_password', validators=[InputRequired(message="Password Required"),
                                                                     EqualTo('password', message="Password did not match!")])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("user name already exist!")


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(message="user Name Required!")])
    password = PasswordField('password', validators=[InputRequired(message="Password Required!"), validate_profile])

class SearchForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(message="user Name Required!")])
    