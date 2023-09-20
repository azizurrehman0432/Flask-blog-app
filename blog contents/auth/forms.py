# Set the encoding to UTF-8
# Import necessary modules and classes
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, ValidationError
from wtforms.validators import Required, Length, Email, EqualTo, Regexp
from ..models import User

# Define a user registration form
class UserRegister(FlaskForm):
    # Define form fields and their validation rules
    username = StringField('Username:', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9]*$', 0, 'Usernames must have only letters and numbers')])
    email = StringField('Email:', validators=[
        Required(), Email(), Length(1, 64)])
    password = PasswordField('Password:', validators=[
        Required(), EqualTo('password2', message='Passwords do not match')])
    password2 = PasswordField('Confirm Password:', validators=[Required()])
    submit = SubmitField('Register')

    # Custom validation method to check for duplicate usernames
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already exists')

    # Custom validation method to check for duplicate email addresses
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('This email address has already been registered')

# Define a user login form
class UserLogin(FlaskForm):
    # Define form fields and their validation rules
    email = StringField('Email:', validators=[
        Required(), Email(), Length(1, 64)])
    password = PasswordField('Password:', validators=[Required(), Length(1, 64)])
    submit = SubmitField('Login')
