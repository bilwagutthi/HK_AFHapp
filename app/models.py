from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('mentor.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('mentor.id'))
)


class Mentor(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    designation = db.Column(db.String(140))
    linkedin = db.Column(db.String(140))
    twitter = db.Column(db.String(140))
    qna= db.relationship ('QnA', backref='answer', lazy='dynamic')
    followed = db.relationship(
        'Mentor', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {} id:>'.format(self.name,str(self.id))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title= db.Column(db.String(100))
    body = db.Column(db.String(500000))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('mentor.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.title)


class Mentee(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    linkedin = db.Column(db.String(140))
    qna= db.relationship ('QnA', backref='question', lazy='dynamic')

    def __repr__(self):
        return '<Mentee {}>'.format(self.name)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

class QnA(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    by = db.Column(db.Integer, db.ForeignKey('mentee.id') )
    to = db.Column(db.Integer, db.ForeignKey('mentor.id') )
    ques = db.Column(db.String(100))
    ans = db.Column(db.String(3000))
    

@login.user_loader
def load_user(id):
    return Mentor.query.get(int(id)) 