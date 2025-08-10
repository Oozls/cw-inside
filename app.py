from flask import Flask, render_template, request, redirect, flash, session, make_response, url_for, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from waitress import serve
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from blake3 import blake3
from PIL import Image
import os, time, cloudinary.uploader, cloudinary.api, cloudinary, requests, logging, sys, json

load_dotenv()




app = Flask(__name__)
CORS(app)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = os.getenv("SECRET_KEY")
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logging.info(f'__file__: {__file__}')
logging.info(f'dir: {os.path.dirname(__file__)}')




mongo = PyMongo()
client = MongoClient(os.getenv("DB_CONNECT"), 27017)
db = client['cwinside']
post_collection = db['post']
user_collection = db['user']
pending_user_collection = db['pending_user']
comment_collection = db['comment']




def record_view(id):
    if 'viewed_post' not in session.keys(): session['viewed_post'] = []
    elif not session['viewed_post']: session['viewed_post'] = []
    
    if id not in session['viewed_post']:
        session['viewed_post'] = session['viewed_post'] + [id]
        post_collection.update_one({'_id':ObjectId(id)}, {'$inc':{'views':1}})
        return True
    else: return False

def isOrange(id):
    user = user_collection.find_one({'_id':ObjectId(id)})
    if user['manager'] == 'orange': return True
    return False

def isBlue(id):
    user = user_collection.find_one({'_id':ObjectId(id)})
    if user['manager'] == 'blue': return True
    return False

def isLogin():
    if 'num' not in session.keys(): return False
    elif not session['num']: return False
    return True

def isAdmin():
    if '_id' not in session.keys(): return False
    user = user_collection.find_one({'_id':ObjectId(session['_id'])})
    if not user: return False
    return user['isAdmin']

def img_to_hash(file):
    file_bytes = file.read()
    file.seek(0)
    hash_name = blake3(file_bytes).hexdigest()
    return hash_name

def unix_to_text(unix_time):
    utc_time = datetime.fromtimestamp(unix_time, timezone.utc)
    kst = timezone(timedelta(hours=9))
    kst_time = utc_time.astimezone(kst)
    return kst_time.strftime('%Y년 %m월 %d일 %H:%M')

def process_post(post, id):
    post['unix_time'] = unix_to_text(post['unix_time'])
    user = user_collection.find_one({'_id':ObjectId(post['user_id'])})

    if post['isAnonymous']: post['user_id'] = '익명의 청붕이'
    else: post['user_id'] = f'{user['num']} {user['name']}'

    type_list = {
            'none': 'none',
            'talk': '잡담',
            'picture': '짤',
            'school': '학교',
            'game': '게임',
            'politics': '정치'
    }
    post['type'] = type_list[post['type']]

    if isOrange(user['_id']) and not post['isAnonymous']: post['manager'] = 'orange'
    elif isBlue(user['_id']) and not post['isAnonymous']: post['manager'] = 'blue'
    else: post['manager'] = 'normal'
    return post

# for file in os.listdir("static/img/emoticon/touhou1"):
#     filename, ext = os.path.splitext(file)
#     print(f"{filename}/{ext}")
#     if ext == '.webp':
#         im = Image.open(os.path.join("static/img/emoticon/touhou1", file)).convert('RGB')
#         im.save(os.path.join("static/img/emoticon/touhou1", filename+'.png'), 'png')

def setup_emoticon():
    folder_path = "static/img/emoticon/touhou1"
    i = 1
    isDone = False
    files = []
    while(not isDone):
        file = None
        if os.path.exists(os.path.join(folder_path, str(i)+'.png')): file = os.path.join(folder_path, str(i)+'.png')
        elif os.path.exists(os.path.join(folder_path, str(i)+'.gif')): file = os.path.join(folder_path, str(i)+'.gif')
        if not file:
            isDone = True
        else:
            files.append('/'+file.replace('\\','/'))
            i += 1
    with open("static/img/emoticon/touhou1.json", "w", encoding="utf-8") as f:
        json.dump(files, f, ensure_ascii=False)
setup_emoticon()




@app.route('/', methods=['GET'])
@app.route('/index')
def index():
    posts = list(post_collection.find().sort('gaechoo',-1))[:5]
    for post in posts:
        process_post(post, post['_id'])
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
    isAnonymous = True if request.form.get('isAnonymous') == "on" else False

    unix_time = time.time()

    img_data = []
    soup = BeautifulSoup(content, 'html.parser')
    imgs = soup.select('img')
    for img in imgs:
        src = os.path.basename(img['src'])
        img_data.append(src)

    post_collection.insert_one({
            "title":title,
            "content":content,
            "unix_time":unix_time,
            "gaechoo":0,
            "user_id": session['_id'],
            "type": request.form['type'],
            "liked_user":[],
            "img": img_data,
            "views":0,
            "isAnonymous": isAnonymous
        })

    return redirect("/list/1")




@app.route('/post/<id>')
def post(id):
    post = post_collection.find_one({"_id":ObjectId(id)})
    if not post:
        return '존재하지 않는 글입니다.', 404

    if not isLogin():
        return '로그인이 필요합니다.', 401
    
    process_post(post, id)
    
    isNewlyViewed = record_view(id)
    if isNewlyViewed: post['views'] += 1

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
    ext = os.path.split(image.filename)[1]
    filename = img_to_hash(image)

    url = url_for('static', filename=f'upload/img/{filename+ext}')
    result = cloudinary.uploader.upload(
            image,
            public_id=filename+ext,
            overwrite=False
    )

    resource = cloudinary.api.resource(filename+ext)
    url = resource['secure_url']

    return jsonify({'url': url})




@app.route('/like/<id>', methods=['POST'])
def like(id):
    post = post_collection.find_one({"_id":ObjectId(id)})
    if not post:
        return "글이 존재하지 않습니다.", 404
    
    if not isLogin():
        return '로그인이 필요합니다.', 401

    user_id = session['_id']
    
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
        process_post(post, post['_id'])

    return render_template("list.html", posts=posts, count=len(list((post_collection.find()))), page=page)

@app.route('/list/<page>/<category>', methods=['GET', 'POST'])
def listCategoryPage(page, category):
    page = int(page)
    if not isLogin():
        return '로그인이 필요합니다.', 401
    if page <= 0:
        return '잘못된 접근입니다.', 403
    
    posts = list(post_collection.find({'type':category}).sort("unix_time", -1))[((page-1)*10):page*10]
    for post in posts:
        process_post(post, post['_id'])

    return render_template("list.html", posts=posts, count=len(list((post_collection.find()))), page=page, category=category)




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