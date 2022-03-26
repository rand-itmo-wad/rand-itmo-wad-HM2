import os

from flask import Flask, render_template, request, url_for, redirect, session
import pymongo
import bcrypt
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "Rand:)"
client = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
db = client.get_database('ITMO')
records = db.users


@app.route('/')
def hello_world():  # put application's code here
    return redirect('/login')


def auth_redirect():
    return redirect('/login')


def signup_core(user, password, update=False):
    if records.find_one({"username": user}):
        message = 'username already existed'
        if update:
            return render_template('profile.html', message=message)
        else:
            return render_template('signup.html', message=message)
    else:
        password_hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        record = {'username': user, 'password': password_hashed}
        if update:
            records.update_one({"username": session.get('username')}, {"$set": record})
        else:
            records.insert_one(record)
        session['username'] = user
        return redirect("/profile")


@app.route('/signup', methods=['post', 'get'])
def signup():
    # check if the user logged in
    if "username" in session:
        return redirect("/profile")
    if request.method == "GET":
        return render_template('signup.html')
    else:
        return signup_core(request.form.get("username"), request.form.get("password"))


@app.route('/login', methods=['post', 'get'])
def login():
    # check if the user logged in
    if "username" in session:
        return redirect("/profile")
    if request.method == "GET":
        return render_template('login.html')
    else:
        user = request.form.get("username")
        password = request.form.get("password")

        user_record = records.find_one({"username": user})
        if user_record:
            user_password = user_record['password']
            if bcrypt.checkpw(password.encode('utf-8'), user_password):
                session['username'] = user
                return redirect('/profile')
        message = 'credentials not correct'
        return render_template('login.html', message=message)


@app.route('/logout')
def logout():
    if "username" in session:
        session.pop('username')
        return auth_redirect()


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    message = None
    if session.get('username'):
        username = session['username']
        try:
            if records.find_one({"username": username})['picture']:
                filename = records.find_one({"username": username})['picture']
            else:
                filename = None
        except:
            filename = None
        if request.method == "POST":
            app_root = os.path.dirname(os.path.abspath(__file__))
            target = os.path.join(app_root, 'static/pictures')

            if not os.path.isdir(target):
                os.mkdir(target)

            filename = secure_filename(request.files.get("picture").filename)
            if request.files.get("picture") and allowed_file(filename):
                destination = os.path.join(target, filename)
                request.files.get("picture").save(destination)
                records.update_one({"username": username}, {"$set": {"picture": filename}})
                message = 'Image uploaded'
            else:
                try:
                    if records.find_one({"username": username})['picture']:
                        filename = records.find_one({"username": username})['picture']
                    else:
                        filename = None
                except:
                    filename = None
                message = 'Image extension is not allowed'
        return render_template('profile.html', destination=filename, message=message, username=username)
    else:
        return auth_redirect()


@app.route('/updateInfo', methods=['POST'])
def update_info():
    if session.get('username'):
        return signup_core(request.form.get("username"), request.form.get("password"), True)
    else:
        return auth_redirect()


@app.route('/display/<filename>', methods=['GET', 'POST'])
def display_image(filename):
    return redirect(url_for('static', filename='pictures/' + filename), code=301)


if __name__ == '__main__':
    app.run()
