import datetime
import os
from flask import Flask, render_template, url_for, request, session, redirect, send_from_directory
from flask_pymongo import PyMongo
import bcrypt
import uuid
from werkzeug.utils import secure_filename
app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'lyxellabs'
app.config['MONGO_URI'] = 'mongodb://127.0.0.1:27017/lyxellabs'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALL_EXECPT'] = set(['exe', 'iso'])


# function for converting file size bytes to MB.... GB... etc
def convert_bytes(num):

    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

# function for checked allowed file types
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] not in app.config['ALL_EXECPT']

mongo = PyMongo(app)

@app.route('/')
#function for login
def index():
    if 'username' in session:
        return redirect(url_for('profile'))
    else:
        return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
#function for uploading file and saving in database
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.split('.')[-1]
            new_filename = str(uuid.uuid4())+'.'+ext
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
            profiles = mongo.db.files
            file_path =  os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            file_size =  convert_bytes(os.stat(file_path).st_size)
            created_at = datetime.datetime.now()
            profiles.insert({'username': session['username'], 'filename': new_filename,'old_filename' : filename,'file_size' :file_size, 'created_at' : created_at })
            return redirect(url_for('profile'))
    return render_template('upload.html')

@app.route('/uploads/<filename>')
#function for viewing files
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)

@app.route('/profile', methods=['POST', 'GET'])
#function for profile after login
def profile():
    if 'username' in session:
        user_data = mongo.db.files.find()
        return render_template('profile.html', user_data = user_data)
    return redirect(url_for('index'))

@app.route('/logout')
#function for logout
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/login', methods=['GET','POST'])
#function for login checking
def login():
    users = mongo.db.users
    login_user = users.find_one({'username' : request.form['username']})
    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password'].encode('utf-8')) == login_user['password'].encode('utf-8'):
            session['username'] = request.form['username']
            return redirect(url_for('index'))

    return 'Invalid username/password combination'

@app.route('/register', methods=['POST', 'GET'])
#function for user registation
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'username' : request.form['username']})
        existing_email = users.find_one({'email': request.form['email']})

        if existing_user is None and existing_email is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'username' : request.form['username'], 'email' : request.form['email'], 'password' : hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        elif existing_email is None:
            return 'Email id is alredy exists!'
        return 'That username already exists!'
    return render_template('register.html')



if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True)