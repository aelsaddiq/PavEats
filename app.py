from flask_migrate import Migrate
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Post, Like, Comment, MenuItem, Poll, PollOption, Vote, PostMedia, Follow, SavedPost
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)

app.config["SECRET_KEY"] = "dev-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["ALLOWED_EXTENSIONS"] = {
    "png", "jpg", "jpeg", "gif",
    "mp4", "mov", "webm"
}

db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already exists. Try logging in.")
            return redirect(url_for("signup"))

        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("feed"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.")
            return redirect(url_for("login"))

        login_user(user)
        return redirect(url_for("feed"))

    return render_template("login.html")

@app.route("/create", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        food_name = request.form.get("food_name")
        rating = int(request.form.get("rating"))
        review_text = request.form.get("review_text")
        meal_period = request.form.get("meal_period")
        post_type = request.form.get("post_type")
        new_post = Post(
            user_id=current_user.id,
            food_name=food_name,
            rating=rating,
            review_text=review_text,
            meal_period=meal_period,
            post_type=post_type
        )

        db.session.add(new_post)
        db.session.commit()

        files = request.files.getlist("media")

        for file in files:
            if file and file.filename != "" and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                saved_filename = f"{current_user.id}_{new_post.id}_{filename}"

                file.save(os.path.join(app.config["UPLOAD_FOLDER"], saved_filename))

                extension = filename.rsplit(".", 1)[1].lower()

                if extension in ["mp4", "mov", "webm"]:
                    media_type = "video"
                else:
                    media_type = "image"

                media = PostMedia(
                    post_id=new_post.id,
                    filename=saved_filename,
                    media_type=media_type
                )

                db.session.add(media)

        db.session.commit()

        return redirect(url_for("feed"))

    return render_template("create_post.html")

@app.route("/toggle-follow/<int:user_id>", methods=["POST"])
@login_required
def toggle_follow(user_id):
    if user_id == current_user.id:
        return redirect(url_for("profile", user_id=user_id))

    existing_follow = Follow.query.filter_by(
        follower_id=current_user.id,
        following_id=user_id
    ).first()

    if existing_follow:
        db.session.delete(existing_follow)
    else:
        new_follow = Follow(
            follower_id=current_user.id,
            following_id=user_id
        )
        db.session.add(new_follow)

    db.session.commit()

    return redirect(url_for("profile", user_id=user_id))


@app.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow(user_id):
    follow = Follow.query.filter_by(
        follower_id=current_user.id,
        following_id=user_id
    ).first()

    if follow:
        db.session.delete(follow)
        db.session.commit()

    return redirect(url_for("profile", user_id=user_id))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/feed")
@login_required
def feed():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("feed.html", posts=posts)


with app.app_context():
    db.create_all()

@app.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    existing_like = Like.query.filter_by(
        user_id=current_user.id,
        post_id=post_id
    ).first()

    if existing_like:
        db.session.delete(existing_like)
    else:
        new_like = Like(user_id=current_user.id, post_id=post_id)
        db.session.add(new_like)

    db.session.commit()
    return redirect(url_for("feed"))

@app.route("/save-post/<int:post_id>", methods=["POST"])
@login_required
def save_post(post_id):
    existing_save = SavedPost.query.filter_by(
        user_id=current_user.id,
        post_id=post_id
    ).first()

    if existing_save:
        db.session.delete(existing_save)
    else:
        saved_post = SavedPost(
            user_id=current_user.id,
            post_id=post_id
        )
        db.session.add(saved_post)

    db.session.commit()

    return redirect(request.referrer or url_for("feed"))

@app.route("/saved")
@login_required
def saved():
    saved_items = SavedPost.query.filter_by(user_id=current_user.id).all()
    posts = [item.post for item in saved_items]

    return render_template("feed.html", posts=posts, page_title="Saved Posts")

@app.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def comment_post(post_id):
    text = request.form.get("comment_text")

    if text:
        new_comment = Comment(
            user_id=current_user.id,
            post_id=post_id,
            text=text
        )

        db.session.add(new_comment)
        db.session.commit()

    return redirect(url_for("feed"))

@app.route("/delete-comment/<int:comment_id>", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != current_user.id and current_user.role != "admin":
        return redirect(url_for("feed"))

    db.session.delete(comment)
    db.session.commit()

    return redirect(request.referrer or url_for("feed"))

@app.route("/menu")
@login_required
def menu():
    date = request.args.get("date")

    if date:
        menu_items = MenuItem.query.filter_by(date=date).all()
    else:
        menu_items = MenuItem.query.order_by(MenuItem.date.desc()).all()

    return render_template("menu.html", menu_items=menu_items)


@app.route("/admin/menu", methods=["GET", "POST"])
@login_required
def admin_menu():
    if current_user.role != "admin":
        return redirect(url_for("feed"))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        meal_period = request.form.get("meal_period")
        station = request.form.get("station")
        date = request.form.get("date")

        item = MenuItem(
            name=name,
            description=description,
            meal_period=meal_period,
            station=station,
            date=date
        )

        db.session.add(item)
        db.session.commit()

        return redirect(url_for("menu"))

    return render_template("admin_menu.html")

@app.route("/polls")
@login_required
def polls():
    polls = Poll.query.order_by(Poll.created_at.desc()).all()

    user_votes = {}

    for poll in polls:
        voted_option = (
            Vote.query
            .join(PollOption)
            .filter(
                Vote.user_id == current_user.id,
                PollOption.poll_id == poll.id
            )
            .first()
        )

        user_votes[poll.id] = voted_option

    return render_template("polls.html", polls=polls, user_votes=user_votes)

@app.route("/admin/polls", methods=["GET", "POST"])
@login_required
def admin_polls():
    if current_user.role != "admin":
        return redirect(url_for("feed"))

    if request.method == "POST":
        question = request.form.get("question")
        options = request.form.getlist("options")

        poll = Poll(question=question)
        db.session.add(poll)
        db.session.commit()

        for option_text in options:
            if option_text.strip():
                option = PollOption(poll_id=poll.id, text=option_text.strip())
                db.session.add(option)

        db.session.commit()
        return redirect(url_for("polls"))

    return render_template("admin_polls.html")


@app.route("/vote/<int:poll_id>", methods=["POST"])
@login_required
def vote(poll_id):
    option_id = request.form.get("option_id")

    poll = Poll.query.get_or_404(poll_id)

    already_voted = (
        Vote.query
        .join(PollOption)
        .filter(
            Vote.user_id == current_user.id,
            PollOption.poll_id == poll.id
        )
        .first()
    )

    if already_voted:
        return redirect(url_for("polls"))

    vote = Vote(user_id=current_user.id, option_id=option_id)
    db.session.add(vote)
    db.session.commit()

    return redirect(url_for("polls"))

@app.route("/clear-vote/<int:poll_id>", methods=["POST"])
@login_required
def clear_vote(poll_id):
    vote = (
        Vote.query
        .join(PollOption)
        .filter(
            Vote.user_id == current_user.id,
            PollOption.poll_id == poll_id
        )
        .first()
    )

    if vote:
        db.session.delete(vote)
        db.session.commit()

    return redirect(request.referrer or url_for("polls"))

@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id and current_user.role != "admin":
        return redirect(url_for("feed"))

    if request.method == "POST":
        post.food_name = request.form.get("food_name")
        post.rating = int(request.form.get("rating"))
        post.review_text = request.form.get("review_text")
        post.meal_period = request.form.get("meal_period")

        db.session.commit()
        return redirect(url_for("feed"))

    return render_template("edit_post.html", post=post)

@app.route("/profile/<int:user_id>")
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)

    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    polls = Poll.query.filter_by(creator_id=user.id).order_by(Poll.created_at.desc()).all()
    votes = Vote.query.filter_by(user_id=user.id).all()

    total_posts = len(posts)
    total_reviews = len([post for post in posts if post.post_type == "review"])
    total_creations = len([post for post in posts if post.post_type == "creation"])
    total_polls = len(polls)
    total_votes = len(votes)
    follower_count = Follow.query.filter_by(following_id=user.id).count()
    following_count = Follow.query.filter_by(follower_id=user.id).count()
    saved_count = SavedPost.query.filter_by(user_id=user.id).count()

    return render_template(
        "profile.html",
        user=user,
        posts=posts,
        polls=polls,
        votes=votes,
        total_posts=total_posts,
        total_reviews=total_reviews,
        total_creations=total_creations,
        total_polls=total_polls,
        total_votes=total_votes,
        follower_count=follower_count,
        following_count=following_count,
        saved_count=saved_count,
    )


@app.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        current_user.name = request.form.get("name")
        current_user.bio = request.form.get("bio")

        image = request.files.get("profile_pic")

        if image and image.filename != "" and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            saved_filename = f"profile_{current_user.id}_{filename}"
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], saved_filename))
            current_user.profile_pic = saved_filename

        db.session.commit()
        return redirect(url_for("profile", user_id=current_user.id))

    return render_template("edit_profile.html")

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@app.route("/user-polls/<int:user_id>")
@login_required
def user_polls(user_id):
    user = User.query.get_or_404(user_id)

    polls = Poll.query.filter_by(
        creator_id=user.id
    ).order_by(Poll.created_at.desc()).all()

    user_votes = {}

    for poll in polls:
        voted_option = (
            Vote.query
            .join(PollOption)
            .filter(
                Vote.user_id == current_user.id,
                PollOption.poll_id == poll.id
            )
            .first()
        )

        user_votes[poll.id] = voted_option

    return render_template(
        "polls.html",
        polls=polls,
        user_votes=user_votes,
        page_title=f"{user.name}'s Polls"
    )

@app.route("/edit-account", methods=["GET", "POST"])
@login_required
def edit_account():

    if request.method == "POST":

        new_email = request.form.get("email")
        new_password = request.form.get("password")

        current_user.email = new_email

        if new_password:
            current_user.password_hash = generate_password_hash(new_password)

        db.session.commit()

        flash("Account updated successfully.")

        return redirect(url_for("settings"))

    return render_template("edit_account.html")

@app.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id and current_user.role != "admin":
        return redirect(url_for("feed"))

    db.session.delete(post)
    db.session.commit()

    return redirect(url_for("feed"))

@app.route("/creations")
@login_required
def creations():
    posts = Post.query.filter_by(post_type="creation").order_by(Post.created_at.desc()).all()
    return render_template("feed.html", posts=posts, page_title="Creations")


with app.app_context():
    db.create_all()

@app.route("/create-poll", methods=["GET", "POST"])
@login_required
def create_poll():

    if request.method == "POST":
        question = request.form.get("question")
        description = request.form.get("description")
        options = request.form.getlist("options")

        poll = Poll(
            question=question,
            description=description,
            creator_id=current_user.id
        )

        db.session.add(poll)
        db.session.commit()

        for option_text in options:
            if option_text.strip():
                option = PollOption(
                    poll_id=poll.id,
                    text=option_text.strip()
                )

                db.session.add(option)

        db.session.commit()

        return redirect(url_for("polls"))

    return render_template("create_poll.html")


if __name__ == "__main__":
    app.run(debug=True)