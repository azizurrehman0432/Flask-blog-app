# coding=utf-8
from flask import render_template, make_response, redirect, url_for, request, flash, abort, g, current_app, json
from datetime import datetime
from . import main
from flask_login import current_user, login_required
from ..models import User, Follow, Topic, Post, TopicFollows, Comments, Messages, Answer, Question, Tag, PostTag
from .forms import UserInfo, UserPasswd, Avatar, TopicForm, PostForm, EditTopic, CommentForm, SearchForm, AskForm
from .. import db
from sqlalchemy import and_, or_
from flask_sqlalchemy import get_debug_queries
import re
import random
from config import Config
import logging
from logging.handlers import SMTPHandler


@main.context_processor
def utility_processor():
    questions = Question.query.order_by(Question.timestamp).limit(5).all()
    tags = Tag.query.all()
    random.shuffle(tags)
    return dict(tags=tags, random=random, search=SearchForm(), questions=questions[::-1])


@main.route('/search/<xxx>', methods=['GET', 'POST'])
def Searchs(xxx):
    sss = '%' + xxx + '%'
    posts = Post.query.filter(
        or_(Post.body.like(sss), Post.head.like(sss))).all()
    return render_template('search.html', posts=posts)


@main.before_app_request
def before_request():
    search = SearchForm()
    if not current_user.is_ban():
        abort(404)
    elif search.validate_on_submit():
        s = search.key1.data
        # return Search(s)
        return redirect(url_for('main.Searchs', xxx=s))
    elif current_user.is_authenticated:
        current_user.ping()
        current_user.noread_messages = (Messages.query.filter_by(
            the_id=current_user.id).filter_by(is_read=False).count() + Messages.query.filter_by(
            post_author_id=current_user.id).filter_by(is_read=False).count() + Messages.query.filter_by(
            q_author_id=current_user.id).filter_by(is_read=False).count())
        db.session.add(current_user)


@main.route('/user/seting/', methods=['GET', 'POST'])
@login_required
def user_seting():
    index = request.cookies.get('xx', 'seting1')
    form = UserInfo()
    if index == 'seting1':
        form = UserInfo()
        if form.validate_on_submit():
            current_user.name = form.realname.data
            current_user.location = form.location.data
            current_user.abortme = form.abortme.data
            db.session.add(current_user)
            flash('settings1')
            return redirect(url_for('main.info_resp'))
        form.realname.data = current_user.name
        form.location.data = current_user.location
        form.abortme.data = current_user.abortme
    if index == 'seting2':
        form = UserPasswd()
        if form.validate_on_submit():
            current_user.password = form.newpassword.data
            db.session.add(current_user)
            flash('settings2')
            return redirect(url_for('main.passwd_resp'))
    if index == 'seting3':
        form = Avatar()
        if form.validate_on_submit():
            img = form.avatar.data
            filename = str(datetime.now()).split(
                '.')[-1] + 'id%d' % current_user.id
            img.save('blog/static/user/avatar/%s.jpg' % filename)
            current_user.avatar = '%s.jpg' % filename
            db.session.add(current_user)
            flash('settings3')
            return redirect(url_for('main.email_resp'))

    return render_template('index.html', user=current_user, index=index, form=form, title='settings', search=SearchForm())


@main.route('/', methods=['GET', 'POST'])
def home():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=10, error_out=False)
    posts = pagination.items[::-1]
    uc = User.query.count()
    pc = Post.query.count()
    qc = Question.query.count()
    ac = Answer.query.count()
    cc = Comments.query.count()
    data = {
        'uc': uc,
        'pc': pc,
        'qc': qc,
        'ac': ac,
        'cc': cc,
        'pagination': pagination,
    }
    return render_template('home.html', data=data, user=current_user, posts=posts[::-1], Tag=Tag, random=random)



@main.route('/user/<id>')
def user_index(id):
    user = User.query.get_or_404(id)
    if not user.ban:
        abort(404)
    c1 = Follow.query.filter_by(follower_id=user.id).count()
    c2 = Follow.query.filter_by(followed_id=user.id).count()
    show = request.cookies.get('show', '1')
    page = request.args.get('page', 1, type=int)
    if show == '1':
        q = Post
    elif show == '2':
        q = Answer
    elif show == '3':
        q = Comments
    elif show == '4':
        q = Question
    pagination = q.query.filter_by(
        author=user.id).order_by(q.timestamp).paginate(
        page, per_page=10, error_out=False)
    posts = pagination.items[::-1]
    return render_template('index.html', show=show, user=user, Topic=Topic, pagination=pagination, posts=posts, index='index,info', c1=c1, c2=c2, Comments=Comments, Post=Post, Question=Question)


@main.route('/all/<id>')
def show_all(id):
    resp = make_response(redirect(url_for('.user_index', id=id)))
    resp.set_cookie('show', '0', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/posts/<id>')
def show_post(id):
    resp = make_response(redirect(url_for('.user_index', id=id)))
    resp.set_cookie('show', '1', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/answer/<id>')
def show_answer(id):
    resp = make_response(redirect(url_for('.user_index', id=id)))
    resp.set_cookie('show', '2', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/comment/<id>')
def show_comment(id):
    resp = make_response(redirect(url_for('.user_index', id=id)))
    resp.set_cookie('show', '3', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/question/<id>')
def show_question(id):
    resp = make_response(redirect(url_for('.user_index', id=id)))
    resp.set_cookie('show', '4', max_age=30 * 24 * 60 * 60)
    return resp



@main.route('/seting/info')
@login_required
def info_resp():
    resp = make_response(redirect(url_for('.user_seting')))
    resp.set_cookie('xx', 'seting1', max_age=60)
    return resp


@main.route('/seting/passwd')
@login_required
def passwd_resp():
    resp = make_response(redirect(url_for('.user_seting')))
    resp.set_cookie('xx', 'seting2', max_age=60)
    return resp


@main.route('/seting/email')
@login_required
def email_resp():
    resp = make_response(redirect(url_for('.user_seting')))
    resp.set_cookie('xx', 'seting3', max_age=60)
    return resp



@main.route('/user/follower-all/<id>')
def user_follower_all(id):
    user = User.query.get_or_404(id)
    all_follower = user.all_follower()
    return render_template('index.html', user=user, index='follower-all,index', all_follower=all_follower)




@main.route('/user/followed-all/<id>')
def user_followed_all(id):
    user = User.query.get_or_404(id)
    all_followed = user.all_follow()
    return render_template('index.html', user=user, index='followed-all,index', all_followed=all_followed)




@main.route('/user/follow/<id>')
@login_required
def user_follow(id):
    user = User.query.get_or_404(id)
    current_user.follow(user)
    flash('关注成功')
    return redirect(url_for('main.user_index', id=user.id))




@main.route('/user/unfollow/<id>')
@login_required
def user_unfollow(id):
    user = User.query.get_or_404(id)
    current_user.unfollow(user)
    flash('已取消关注')
    return redirect(url_for('main.user_index', id=user.id))



@main.route('/topics', methods=['GET', 'POST'])
def topics():
    topics = Topic.query.filter_by(activation=True).all()
    form = TopicForm()
    if current_user.is_authenticated and form.validate_on_submit():
        t = Topic(topic=form.topic_name.data,
                  info=form.topic_info.data, author=current_user.id)
        db.session.add(t)
        db.session.commit()
        img = form.topic_img.data
        img.save('blog/static/topics/%s.jpg' % t.id)
        t.img = '%s.jpg' % t.id
        db.session.add(t)
        return redirect(url_for('main.topics'))
    return render_template('topics/topics.html', form=form, topics=topics, Post=Post)




@main.route('/topics/<topic>', methods=['GET', 'POST'])
def topic(topic):
    form = EditTopic()
    t = Topic.query.filter_by(topic=topic).first()
    if not t or not t.activation:
        abort(404)
    if form.validate_on_submit():
        t.info = form.topic_info.data
        db.session.add(t)
        return redirect(url_for('main.topic', topic=t.topic))
    t.ping()
    form.topic_info.data = t.info
    f = None
    if current_user.is_authenticated:
        f = current_user.is_follow_t(t)
    return render_template('topics/topic.html', t=t, f=f, title=topic, Post=Post, form=form, Comments=Comments)



@main.route('/new-post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if Topic.query.all() == []:
        flash('posted')
        return redirect(url_for('main.topics'))
    if request.method == 'POST':
        p = Post(author=current_user.id, tpoic=form.topic.data,
                 head=form.head.data, body=form.postbody.data)
        # data = json.loads(request.form.get('data'))
        # body = data['body']
        db.session.add(p)
        db.session.commit()
        if form.tag.data:
            tags = re.findall(r'#(.+?)\s', form.tag.data)
            for tag in tags:
                t = Tag.query.filter_by(tag_name=tag).first()
                if t:
                    pt = PostTag(post_id=p.id, tags_id=t.id)
                    db.session.add(pt)
                else:
                    t = Tag(tag_name=tag)
                    db.session.add(t)
                    db.session.commit()
                    pt = PostTag(post_id=p.id, tags_id=t.id)
                    db.session.add(pt)
        return redirect(url_for('main.post', id=p.id))
    topics = Topic.query.order_by(Topic.id).all()
    return render_template('topics/new_post.html', form=form, topics=topics)


@main.route('/delete-post/<id>')
@login_required
def delete_post(id):
    p = Post.query.get_or_404(id)
    topic = p.topic.topic
    user = User.query.filter_by(id=p.author).first()
    if user.is_self(current_user):
        db.session.delete(p)
        cs = Comments.query.filter_by(post_id=p.id).all()
        for c in cs:
            db.session.delete(c)
        db.session.commit()
        flash('deleted')
        return redirect(url_for('main.topic', topic=topic))
    else:
        flash('error')
        return redirect(url_for('main.topic', topic=topic))



@main.route('/post/<id>', methods=['GET', 'POST'])
def post(id):
    commentform = CommentForm()
    p = Post.query.get_or_404(id)
    if current_user.is_authenticated and request.method == 'POST':
        comment = Comments(author=current_user.id,
                           post_id=p.id, body=commentform.body.data, post_author_id=p.author)
        db.session.add(comment)
        db.session.commit()
        x = re.match('.*@(.+)&nbsp;.*', commentform.body.data)
        if x:
            username = x.group(1)
            u = User.query.filter_by(username=username).first()
            if u:
                mes = Messages(post_author_id=p.author, the_id=u.id, from_id=current_user.id,
                               comment_id=p.id, post_id=p.id, body_id=comment.id)
                db.session.add(mes)
        else:
            mes = Messages(post_author_id=p.author, from_id=current_user.id,
                           post_id=p.id, body_id=comment.id)
            db.session.add(mes)
        return redirect(url_for('main.post', id=p.id))
    p.ping()
    author = User.query.filter_by(id=p.author).first()
    comments = Comments.query.filter_by(post_id=p.id).all()
    return render_template('topics/post.html', p=p, author=author, commentform=commentform, comments=comments)


@main.route('/topic/follow/<topic>')
@login_required
def follow_topic(topic):
    t = Topic.query.filter_by(topic=topic).first()
    if t is None:
        abort(404)
    current_user.follow_t(t)
    return redirect(url_for('main.topic', topic=topic))


@main.route('/topic/unfollow/<topic>')
@login_required
def unfollow_topic(topic):
    t = Topic.query.filter_by(topic=topic).first()
    if t is None:
        abort(404)
    current_user.unfollow_t(t)
    return redirect(url_for('main.topic', topic=topic))


@main.route('/user/messages')
@login_required
def messages():
    # messages = Comments.query.filter_by(
    #     post_author_id=current_user.id).all()[::-1]
    post_ms = Messages.query.filter_by(
        post_author_id=current_user.id).filter_by(is_read=False).all()
    at_ms = Messages.query.filter_by(
        the_id=current_user.id).filter_by(is_read=False).all()
    a_ms = Messages.query.filter_by(
        q_author_id=current_user.id).filter_by(is_read=False).all()
    read_ms = Messages.query.filter_by(is_read=True).all()
    return render_template('user/messages.html', a_ms=a_ms, Question=Question, post_ms=post_ms, at_ms=at_ms, User=User, Post=Post, Comments=Comments, read_ms=read_ms)


@main.route('/user/read_all_messages')
@login_required
def read_all_messages():
    Messages.read_all(current_user.id)
    return redirect(url_for('main.messages'))


@main.route('/user/messages/read/<id>')
@login_required
def read_message(id):
    ms = Messages.query.get_or_404(id)
    ms.read()
    return redirect(url_for('main.post', id=ms.post_id))


@main.route('/user/messagess/read/<id>')
@login_required
def read_messages(id):
    ms = Messages.query.get_or_404(id)
    ms.read()
    return redirect(url_for('main.question', id=ms.q_id))


@main.route('/ask', methods=['GET', 'POST'])
def ask():
    qs = Question.query.order_by(Question.timestamp).all()
    form = AskForm()
    if request.method == 'POST':
        q = Question(author=current_user.id,
                     title=form.title.data, body=form.body.data)
        db.session.add(q)
        flash('done')
        return redirect(url_for('main.ask'))
    return render_template('ask/ask_index.html', qs=qs, form=form, User=User)


@main.route('/sak/question/<int:id>', methods=['GET', 'POST'])
def question(id):
    q = Question.query.get_or_404(id)
    q.read()
    commentform = CommentForm()
    answers = Answer.query.filter_by(q_id=id).all()
    if current_user.is_authenticated and commentform.validate_on_submit():
        a = Answer(q_id=id, q_author_id=q.author,
                   author=current_user.id, body=commentform.body.data)
        db.session.add(a)
        x = re.match('.*@(.+)\s.*', commentform.body.data)
        if x:
            username = x.group(1)
            u = User.query.filter_by(username=username).first()
            if u:
                mes = Messages(q_author_id=q.author, the_id=u.id, from_id=current_user.id,
                               comment_id=q.id, q_id=q.id, body_id=a.id)
                db.session.add(mes)
        else:
            mes = Messages(q_author_id=q.author, from_id=current_user.id,
                           q_id=q.id, body_id=a.id)
            db.session.add(mes)
        return redirect(url_for('main.question', id=id))
    return render_template('ask/question.html', q=q, User=User, commentform=commentform, answers=answers)


@main.route('/sak/question/app/<int:id>%<int:q_id>')
@login_required
def app_answer(id, q_id):
    a = Answer.query.get_or_404(id)
    if a:
        a.up()
    return redirect(url_for('main.question', id=q_id))


@main.route('/sak/question/opp/<int:id>%<int:q_id>')
@login_required
def opp_answer(id, q_id):
    a = Answer.query.get_or_404(id)
    if a:
        a.down()
    return redirect(url_for('main.question', id=q_id))


@main.route('/sak/question<int:id>/answer<int:ad>')
@login_required
def is_answer(id, ad):
    q = Question.query.get_or_404(id)
    q.answer = ad
    a = Answer.query.get_or_404(ad)
    a.adopt = True
    db.session.add(q)
    db.session.add(a)
    return redirect(url_for('main.question', id=id))


@main.route('/post/tag/<tag>', methods=['GET', 'POST'])
def post_for_tag(tag):
    tag = Tag.query.filter_by(id=tag).first()
    if not tag:
        abort(404)
    posts = tag.posts.all()
    tag = tag.tag_name
    return render_template('post_for_tag.html', posts=posts, tag=tag)
