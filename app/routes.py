from app import app, db
from flask import render_template, flash, redirect,  url_for, request
from app.forms import MentorLoginForm, MentorRegistrationForm, EditProfileForm, EmptyForm, PostForm
from flask_login import current_user, login_user, logout_user, login_required 
from app.models import Mentor, Post
from werkzeug.urls import url_parse

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])

def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, body=form.body.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
        page = request.args.get('page', 1, type=int)
        posts = current_user.followed_posts().paginate(
            page, app.config['POSTS_PER_PAGE'], False)
        next_url = url_for('index', page=posts.next_num) \
            if posts.has_next else None
        prev_url = url_for('index', page=posts.prev_num) \
            if posts.has_prev else None
        return render_template('index.html', title='Home', form=form,
                            posts=posts.items, next_url=next_url,
                            prev_url=prev_url)
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def mentorLogin():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = MentorLoginForm()
    if form.validate_on_submit():
        user = Mentor.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('mentorLogin'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
            print('\n\n\n Redireted to index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def mentorRegister():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = MentorRegistrationForm()
    if form.validate_on_submit():
        user = Mentor(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('mentorLogin'))
    
    return render_template('register.html', title='Register', form=form)



@app.route('/mentor/<id>')
@login_required
def mentor(id):
    user = Mentor.query.filter_by(id=id).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)



@app.route('/follow/<id>', methods=['POST'])
@login_required
def follow(id):
    form = EmptyForm()
    if form.validate_on_submit():
        user = Mentor.query.filter_by(id=id).first()
        if user is None:
            flash('User {} not found.'.format(user.name))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('mentor', id=id))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(user.name))
        return redirect(url_for('mentor', id=id))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<id>', methods=['POST'])
@login_required
def unfollow(id):
    form = EmptyForm()
    if form.validate_on_submit():
        user = Mentor.query.filter_by(id=id).first()
        if user is None:
            flash('User {} not found.'.format(user.name))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('mentor', id=id))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(user.name))
        return redirect(url_for('mentor', id=id))
    else:
        return redirect(url_for('index'))

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title='Explore', posts=posts.items,
                          next_url=next_url, prev_url=prev_url)