# coding=utf-8
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField, PasswordField, ValidationError, TextAreaField, SelectField
from wtforms.validators import Required, Length, Email, EqualTo, Regexp
from flask_login import current_user
from ..models import Topic
from flask_uploads import UploadSet, IMAGES

images = UploadSet('images', IMAGES)

class UserInfo(FlaskForm):
    realname = StringField('Real Name', validators=[Length(1, 64)])
    location = StringField('Location', validators=[Length(1, 64)])
    about_me = TextAreaField('About Me', validators=[Length(1, 64)])
    submit = SubmitField('Submit')

class UserPasswd(FlaskForm):
    oldpassword = PasswordField('Old Password', validators=[Required()])
    newpassword = PasswordField(
        'New Password', validators=[Required(), EqualTo('newpassword2', message='Passwords must match')])
    newpassword2 = PasswordField('Confirm New Password', validators=[Required()])
    submit = SubmitField('Submit')

    def validate_oldpassword(self, field):
        if not current_user.verify_password(field.data):
            raise ValidationError('Incorrect password')

class Avatar(FlaskForm):
    avatar = FileField('Upload Avatar', validators=[
        FileRequired(), FileAllowed(['jpg', 'png'], 'Only images are allowed')])
    submit = SubmitField('Submit')

class TopicForm(FlaskForm):
    topic_name = StringField('Topic Name', validators=[Required(), Length(1, 64)])
    topic_info = TextAreaField('Topic Description')
    topic_img = FileField('Topic Image', validators=[
        FileRequired(), FileAllowed(['jpg', 'png'], 'Only images are allowed')])
    submit1 = SubmitField('Submit')

class PostForm(FlaskForm):
    head = StringField('Title', validators=[Required(), Length(1, 64)])
    postbody = TextAreaField('Content', validators=[Required()])
    tag = StringField(
        'Tags', render_kw={'placeholder': 'Tags must start with "#" and end with a space. You can add multiple tags at once.'})
    topic = SelectField('Belongs to Topic', coerce=int)
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.topic.choices = [(t.id, t.topic)
                              for t in Topic.query.order_by(Topic.id).all()]

    def validate_tag(self, field):
        if '#' not in field.data or ' ' not in field.data:
            raise ValidationError('Tags must start with "#" and end with a space.')

class EditTopic(FlaskForm):
    topic_info = TextAreaField('Topic Description')
    submit1 = SubmitField('Submit')

class CommentForm(FlaskForm):
    body = TextAreaField('Content')
    submit = SubmitField('Post')

class SearchForm(FlaskForm):
    key1 = StringField('Search', validators=[Length(1, 64)], render_kw={
                       'placeholder': 'Enter a keyword'})
    search = SubmitField('Search')

class AskForm(FlaskForm):
    title = StringField('Title', validators=[Required(), Length(1, 64)])
    body = TextAreaField('Question Description', validators=[Required()])
    submit1 = SubmitField('Submit')

class ManageSearch(FlaskForm):
    key = StringField('', validators=[Length(1, 64)])
    search = SubmitField('Search')
