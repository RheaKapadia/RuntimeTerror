# FLASK Tutorial 1 -- We show the bare bones code to get an app up and running

# imports
import os  # os is used to get environment variables IP & PORT
from flask import Flask  # Flask is the web app that we will customize
from flask import render_template
from flask import request
from flask import redirect, url_for
from database import db
from models import Post as Post
from models import User as User
from models import Comment as Comment
import bcrypt
from flask import session
from forms import RegisterForm, LoginForm, CommentForm

app = Flask(__name__)  # create an app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///runtime_terror_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'SE3155'
#  Bind SQLAlchemy db object to this Flask app
db.init_app(app)
# Setup models
with app.app_context():
    db.create_all()  # run under the app context


# @app.route is a decorator. It gives the function "index" special powers.
# In this case it makes it so anyone going to "your-url/" makes this function
# get called. What it returns is what is shown as the web page

@app.route('/index')
def index():
    # check if a  user is saved in session
    if session.get('user'):
        # retrieve posts from database
        posts = db.session.query(Post).all()

        currentuser = session['user']
        # return render_template('index.html', posts=posts, user=user, currentuser=currentuser)
        return render_template('index.html', posts=posts, user=session['user'])
    else:
        return render_template('login.html')


@app.route('/')
@app.route('/login', methods=['POST', 'GET'])
def login():
    login_form = LoginForm()
    # validate_on_submit only validates using POST
    if login_form.validate_on_submit():
        # we know user exists. We can use one()
        the_user = db.session.query(User).filter_by(email=request.form['email']).one()
        # user exists check password entered matches stored password
        if bcrypt.checkpw(request.form['password'].encode('utf-8'), the_user.password):
            # password match add user info to session
            session['user'] = the_user.first_name
            session['user_id'] = the_user.id
            # render view
            return redirect(url_for('index'))

        # password check failed
        # set error message to alert user
        login_form.password.errors = ["Incorrect username or password."]
        return render_template("login.html", form=login_form)
    else:
        # form did not validate or GET request
        return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    # check if a user is saved in session
    if session.get('user'):
        session.clear()

    return redirect(url_for('login'))


@app.route('/posts')
def get_posts():
    # check if a user is saved in session
    if session.get('user'):
        # retrieve posts from database
        my_posts = db.session.query(Post).filter_by(user_id=session['user_id']).all()

        return render_template('posts.html', posts=my_posts, user=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/posts/<post_id>')
def get_post(post_id):
    # check if a user is saved in session
    if session.get('user'):
        # retrieve posts from database
        my_post = db.session.query(Post).filter_by(id=post_id, user_id=session['user_id']).one()

        # create a comment form object
        form = CommentForm()

        return render_template('post.html', post=my_post, user=session['user'], form=form, likes=my_post.likes)
    else:
        return redirect(url_for('login'))


@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if session.get('user'):
        # check method used for request
        if request.method == 'POST':
            # create title data
            title = request.form['title']

            # get post data
            text = request.form['postText']

            # create date stamp
            from datetime import date
            today = date.today()

            likes = 0

            # format date mm/dd/yyyy
            today = today.strftime('%m-%d-%Y')
            new_record = Post(title, text, today, session['user_id'], likes)
            db.session.add(new_record)
            db.session.commit()

            return redirect(url_for('get_posts'))
        else:
            # GET request - show new post form
            return render_template('newPost.html', user=session['user'])

    else:
        # user is not in session redirect ot login
        return redirect(url_for('login'))


@app.route("/posts/delete/<post_id>", methods=['POST'])
def delete_post(post_id):
    # check if a user is saved in session
    if session.get('user'):
        # retrieve post from database
        my_post = db.session.query(Post).filter_by(id=post_id).one()
        db.session.delete(my_post)
        db.session.commit()

        return redirect(url_for('get_posts'))
    else:
        # user is not in session redirect to login
        return redirect(url_for('login'))


@app.route('/posts/edit/<post_id>', methods=['GET', 'POST'])
def update_post(post_id):
    if session.get('user'):
        # check method used for request
        if request.method == 'POST':
            # get title data
            title = request.form['title']
            # get post data
            text = request.form['postText']
            post = db.session.query(Post).filter_by(id=post_id).one()
            # update post data
            post.title = title
            post.text = text
            # update post in DB
            db.session.add(post)
            db.session.commit()

            return redirect(url_for('get_posts'))
        else:
            # GET request= show new post form to edit post
            # retrieve post from database
            my_post = db.session.query(Post).filter_by(id=post_id).one()

        return render_template('newPost.html', post=my_post, user=session['user'])
    else:
        # user is not in session redirect to login
        return redirect(url_for('login'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()

    if request.method == 'POST' and form.validate_on_submit():
        # salt and hash password
        h_password = bcrypt.hashpw(
            request.form['password'].encode('utf-8'), bcrypt.gensalt())
        # get entered user data
        first_name = request.form['firstname']
        last_name = request.form['lastname']
        # create user model
        new_user = User(first_name, last_name, request.form['email'], h_password)
        # add user to database and commit
        db.session.add(new_user)
        db.session.commit()
        # save the user's name to the session
        session['user'] = first_name
        session['user_id'] = new_user.id  # access id value from user model of this newly added user
        # show user dashboard view
        return redirect(url_for('get_posts'))

    # something went wrong - display register view
    return render_template('register.html', form=form)


@app.route('/posts/<post_id>/comment', methods=['POST'])
def new_comment(post_id):
    if session.get('user'):
        comment_form = CommentForm()
        # validate_on_submit only validates using POST
        if comment_form.validate_on_submit():
            # get comment data
            comment_text = request.form['comment']
            new_record = Comment(comment_text, int(post_id), session['user_id'])
            db.session.add(new_record)
            db.session.commit()

        return redirect(url_for('get_post', post_id=post_id))

    else:
        return redirect(url_for('login'))


@app.route('/posts/<post_id>', methods=['GET', 'POST'])
def like_post(post_id):
    if session.get('user'):

        post = db.session.query(Post).filter_by(id=post_id).one()
        # update post data
        post.likes += 1
        # likes = post.likes + 1
        # post.likes = likes

        # update post in DB
        # db.session.add(post)
        # db.session.merge(post)
        db.session.commit()

        return redirect(url_for('get_post', post_id=post_id))
    else:
        # user is not in session redirect to login
        return redirect(url_for('login'))
#
# @app.route('/newPoll', methods=['GET', 'POST'])
# def new_poll():
#     if session.get('user'):
#         # check method used for request
#         if request.method == 'POST':
#             # create title data
#             title = request.form['title']
#
#             # get post data
#             text = request.form['postText']
#
#             # create date stamp
#             from datetime import date
#             today = date.today()
#
#             # format date mm/dd/yyyy
#             today = today.strftime('%m-%d-%Y')
#             new_record = Post(title, text, today, session['user_id'])
#             db.session.add(new_record)
#             db.session.commit()
#
#             return redirect(url_for('get_posts'))
#         else:
#             # GET request - show new post form
#             return render_template('newPost.html', user=session['user'])
#
#     else:
#         # user is not in session redirect ot login
#         return redirect(url_for('login'))


app.run(host=os.getenv('IP', '127.0.0.1'), port=int(os.getenv('PORT', 5000)), debug=True)

# To see the web page in your web browser, go to the url,
#   http://127.0.0.1:5000

# Note that we are running with "debug=True", so if you make changes and save it
# the server will automatically update. This is great for development but is a
# security risk for production.
