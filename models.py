from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="student")
    bio = db.Column(db.Text)
    profile_pic = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    followers = db.relationship(
    "Follow",
    foreign_keys="[Follow.following_id]",
    backref="following_user",
    lazy=True
)

following = db.relationship(
    "Follow",
    foreign_keys="[Follow.follower_id]",
    backref="follower_user",
    lazy=True
)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    food_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    meal_period = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    post_type = db.Column(db.String(20), default="review")
    user = db.relationship('User', backref='posts')

class PostMedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    filename = db.Column(db.String(200), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)

    post = db.relationship("Post", backref="media")

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))

    user = db.relationship("User", backref="likes")
    post = db.relationship("Post", backref="likes")


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="comments")
    post = db.relationship("Post", backref="comments")

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    meal_period = db.Column(db.String(20), nullable=False)
    station = db.Column(db.String(80))
    date = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(200), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    creator = db.relationship("User", backref="polls")
    description = db.Column(db.Text)
    options = db.relationship("PollOption", backref="poll", cascade="all, delete-orphan")


class PollOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"))
    text = db.Column(db.String(150), nullable=False)

    votes = db.relationship("Vote", backref="option", cascade="all, delete-orphan")


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    option_id = db.Column(db.Integer, db.ForeignKey("poll_option.id"))
    poll_option = db.relationship("PollOption", overlaps="option")
    user = db.relationship("User", backref="votes")

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    follower_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    following_id = db.Column(db.Integer, db.ForeignKey("user.id"))

class SavedPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))

    user = db.relationship("User", backref="saved_posts")
    post = db.relationship("Post", backref="saved_by")