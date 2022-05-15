from flask import render_template, url_for, flash, redirect, request, abort
from . import main
import requests
from ..models import User, Post, Comment
from .forms import UpdateProfile, PostForm, CommentForm, subscription_form
from .. import db, photos
from flask_login import login_user, current_user, logout_user, login_required
import markdown2
from flask_mail import Message
from .. import mail, MAIL_USERNAME


@main.route("/", methods=['GET', 'POST'])
@main.route("/index", methods=['GET', 'POST'])
def home():

    form = subscription_form()
    if form.validate_on_submit():
        subemail = form.email.data
        senderemail = MAIL_USERNAME
        msg = Message('Hey there.', sender=senderemail, recipients=subemail)
        msg.html = '<h2>Welcome to YourQuote.</h2> <p>YourBlog is a personal blogging website where you can create and share your opinions and other users can read and comment on them. Additionally, add a feature that displays random quotes to inspire your users.</p>'
        mail.send(msg)
        flash('You have been added to our subscription', 'success')
        return redirect(url_for('main.index'))

    return render_template('index.html',form=form)



@main.route("/user/<uname>")
@login_required
def profile(uname):
    user = User.query.filter_by(username=uname).first()
    if user is None:
        abort(404)
    posts = Post.query.filter_by(user_id=current_user.id).all()
    return render_template('profile/profile.html', title='Account', user=user, posts=posts)


@main.route('/user/<uname>/update', methods=['GET', 'POST'])
@login_required
def update_profile(uname):
    user = User.query.filter_by(username=uname).first()
    if user is None:
        abort(404)

    form = UpdateProfile()

    if form.validate_on_submit():
        user.bio = form.bio.data

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('.profile', uname=user.username, title='Update Profile'))

    return render_template('profile/update.html', form=form)


@main.route('/user/<uname>/update/pic', methods=['POST'])
@login_required
def update_pic(uname):
    user = User.query.filter_by(username=uname).first()
    if 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        path = f'photos/{filename}'
        user.image_file = path
        db.session.commit()
    return redirect(url_for('main.profile', uname=uname))


@main.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data,
                    author=current_user, upvotes=0, downvotes=0)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created', 'success')
        return redirect(url_for('main.index'))
    return render_template('create_post.html', title='New Blog', form=form, legend='New Blog')


@main.route("/post/<int:post_id>", methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)

    if request.args.get("upvote"):
        post.upvotes += 1
        db.session.add(post)
        db.session.commit()
        return redirect("/post/{post_id}".format(post_id=post.id))

    elif request.args.get("downvote"):
        post.downvotes += 1
        db.session.add(post)
        db.session.commit()
        return redirect("/post/{post_id}".format(post_id=post.id))

    form = CommentForm()
    if form.validate_on_submit():
        comment = form.text.data

        new_comment = Comment(content=comment, post_id=post.id)

        new_comment.save_comment()
    comments = Post.get_comments(post)

    return render_template('post.html', title=post.title, post=post, comments=comments, form=form)


@main.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated', 'success')
        return redirect(url_for('main.post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Blog')


@main.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('main.index'))
