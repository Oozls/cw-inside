from flask import Flask, render_template, request, redirect, flash, session, make_response, url_for, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from waitress import serve
from datetime import datetime, timezone, timedelta
from werkzeug.utils import secure_filename
import os, time, json

load_dotenv()




app = Flask(__name__)
CORS(app)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = os.getenv("SECRET_KEY")




mongo = PyMongo()
client = MongoClient(os.getenv("DB_CONNECT"), 27017)
db = client['cwinside']
post_collection = db['post']
user_collection = db['user']
pending_user_collection = db['pending_user']
comment_collection = db['comment']




def isLogin():
    if 'num' not in session.keys(): return False
    elif not session['num']: return False
    return True

def isAdmin():
    if '_id' not in session.keys():
        return False

    user = user_collection.find_one({'_id':ObjectId(session['_id'])})

    if not user: return False

    return user['isAdmin']


def unix_to_text(unix_time):
    utc_time = datetime.fromtimestamp(unix_time, timezone.utc)
    kst = timezone(timedelta(hours=9))
    kst_time = utc_time.astimezone(kst)
    return kst_time.strftime('%Y년 %m월 %d일 %H:%M')




@app.route('/', methods=['GET'])
@app.route('/index')
def index():
    posts = list(post_collection.find().sort('gaechoo',-1))[:5]
    for post in posts:
        post['unix_time'] = unix_to_text(post['unix_time'])
        user = user_collection.find_one({'_id':ObjectId(post['user_id'])})
        post['user_id'] = f'{user['num']} {user['name']}'
    return render_template('index.html', posts=posts)




@app.route('/logout', methods=['POST'])
def logout():
    session.pop('num', None)
    session.pop('name', None)
    session.pop('_id', None)
    return redirect('/')




@app.route('/write')
def write():
    if not isLogin(): return redirect('/login')
    else: return render_template('write.html')




@app.route('/post_action', methods=['POST'])
def postAction():
    if not isLogin():
        flash('로그인 후 글을 작성해주세요.')
        return redirect("/write")

    title = request.form['title']
    content = request.form.get('content')

    unix_time = time.time()

    post_collection.insert_one(
        {
            "title":title,
            "content":content,
            "unix_time":unix_time,
            "gaechoo":0,
            "user_id":session['_id'],
            "liked_user":[]
        })
    return redirect("/list/1")




@app.route('/post/<id>')
def post_id(id):
    post = post_collection.find_one({"_id":ObjectId(id)})
    if not post:
        return '존재하지 않는 글입니다.', 404

    if not isLogin():
        return '로그인이 필요합니다.', 401
    
    post['unix_time'] = unix_to_text(post['unix_time'])
    user = user_collection.find_one({'_id':ObjectId(post['user_id'])})
    post['user_id'] = f'{user['num']} {user['name']}'

    comments = list(comment_collection.find({'post_id':id}).sort("unix_time", -1))
    for comment in comments:
        comment['unix_time'] = unix_to_text(comment['unix_time'])
        user1 = user_collection.find_one({'_id':ObjectId(comment['user_id'])})
        comment['user_id'] = f'{user1['num']} {user1['name']}'
    return render_template("post.html", post=post, comments=comments)




@app.route('/upload_image', methods=['POST'])
def upload_image():
    if not isLogin():
        return '로그인이 필요합니다.', 401

    image = request.files['image']
    filename = secure_filename(image.filename)
    image.save(os.path.join('static/upload/img', filename))
    url = url_for('static', filename=f'upload/img/{filename}')
    return jsonify({'url': url})




@app.route('/like/<id>', methods=['POST'])
def like(id):
    post = post_collection.find_one({"_id":ObjectId(id)})
    if not post:
        return "글이 존재하지 않습니다.", 404
    
    if not isLogin():
        return '로그인이 필요합니다.', 401

    user_id = session['_id']

    if 'liked_user' not in post.keys():
        post_collection.update_one({"_id":ObjectId(id)},{'$set': {'liked_user':[]}})
    
    post = post_collection.find_one({"_id":ObjectId(id)})
    liked_user = post['liked_user']

    if user_id in liked_user:
        post_collection.update_one(
            {'_id': ObjectId(id)},
            {'$inc': {'gaechoo': -1}}
        )
        liked_user.remove(user_id)
        post_collection.update_one({"_id":ObjectId(id)},{'$set': {'liked_user': liked_user}})
    else:
        post_collection.update_one(
            {'_id': ObjectId(id)},
            {'$inc': {'gaechoo': +1}}
        )
        liked_user.append(user_id)
        post_collection.update_one({"_id":ObjectId(id)},{'$set': {'liked_user': liked_user}})

    return redirect('/post/'+id)




@app.route('/write_comment/<id>', methods=['POST'])
def write_comment(id):
    post = post_collection.find_one({"_id":ObjectId(id)})
    if not post:
        return "글이 존재하지 않습니다.", 404
    if not isLogin():
        return '로그인이 필요합니다.', 401
    
    comment_collection.insert_one({
        'post_id': id,
        'user_id': session['_id'],
        'content': request.form['content'],
        'unix_time': time.time()
    })
    return redirect(f'/post/{id}')




@app.route('/list/<page>', methods=['GET', 'POST'])
def listPage(page):
    page = int(page)
    if not isLogin():
        return '로그인이 필요합니다.', 401
    if page <= 0:
        return '잘못된 접근입니다.', 403

    posts = list(post_collection.find().sort("unix_time", -1))[((page-1)*10):page*10]
    for post in posts:
        post['unix_time'] = unix_to_text(post['unix_time'])
        user = user_collection.find_one({'_id':ObjectId(post['user_id'])})
        post['user_id'] = f'{user['num']} {user['name']}'
    return render_template("list.html", posts=posts, count=len(list((post_collection.find()))), page=page)




@app.route('/login', methods=['GET', 'POST'])
def loginRedirect():
    if not isLogin(): return render_template('login.html')
    else: return render_template('/')
    



@app.route('/request_login', methods=['POST'])
def request_login():
    num = request.form['num']
    name = request.form['name']
    password = request.form['password']

    user = user_collection.find_one({'num': num})
    if not user:
        flash("가입되지 않은 학번입니다.")
        return redirect('/login')
    elif user['name'] != name:
        flash("학번과 이름이 일치하지 않습니다.")
        return redirect('/login')
    elif user['password'] != password:
        flash("비밀번호가 일치하지 않습니다.")
        return redirect('/login')
    
    session['_id'] = str(user['_id'])
    session['num'] = user['num']
    session['name'] = user['name']
    return redirect('/')




@app.route('/signup', methods=['GET', 'POST'])
def signUp():
    if isLogin(): return redirect('/')
    return render_template('signup.html')




@app.route('/signup_register', methods=['POST'])
def signup_register():
    if isLogin(): return redirect('/')

    num = request.form['num']
    name = request.form['name']
    password = request.form['password']
    password2 = request.form['password']

    def failed(msg):
        flash(msg)
        return redirect('/signup')

    if not num.isdigit(): return failed('학번이 형식에 맞지 않습니다.')
    elif num[0] != '1' and num[0] != '2' and num[0] != '3': return failed('학번이 형식에 맞지 않습니다.')
    elif int(num) < 1101 or int(num) >= 3900: return failed('학번이 형식에 맞지 않습니다.')

    if password != password2: return failed("재입력된 비밀번호가 불일치합니다.")
    
    if not password.isalnum(): return failed("비밀번호의 형식이 올바르지 않습니다. (영한, 숫자 가능)")

    num_user = user_collection.find_one({'num': num})
    if num_user: return failed("이미 가입된 학번입니다.")
    
    pending_user_collection.insert_one({
        "num":num,
        "name":name,
        "password":password,
        "unix_time":time.time(),
        "isAdmin":False
    })

    flash("관리자 허가를 기다려주세요.")
    return redirect('/login')




@app.route('/confirm')
def confirm():
    if not isLogin(): return '로그인이 필요합니다.', 401
    elif not isAdmin(): return '관리자 권한이 필요합니다.', 401

    accounts = list(pending_user_collection.find())
    return render_template('confirm.html', accounts=accounts)




@app.route('/confirm_account', methods=['POST'])
def confirm_account():
    _id = request.form['_id']
    user = pending_user_collection.find_one({"_id":ObjectId(_id)})
    pending_user_collection.delete_one({"_id":ObjectId(_id)})
    user_collection.insert_one(user)
    return redirect('/confirm')




if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8000)