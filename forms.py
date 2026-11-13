from flask_wtf import FlaskForm
from wtforms import PasswordField, RadioField, StringField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from constants import AVATARS

class SignupForm(FlaskForm):
    name = StringField('Your name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    confirm = PasswordField(
        'Confirm password',
        validators=[DataRequired(), EqualTo('password', message='Passwords must match.')]
    )

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class HeroForm(FlaskForm):
    hero_name = StringField('Hero name', validators=[DataRequired(), Length(min=2, max=20)])
    avatar_id = RadioField(
        'Avatar',
        coerce=str,
        choices=[(key, emoji) for key, emoji in AVATARS.items()],
        validators=[DataRequired()]
    )