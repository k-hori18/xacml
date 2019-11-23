from flask import Flask, render_template, request, session, redirect
import mysql.connector
#from werkzeug import secure_filename
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from datetime import datetime
from neo4jrestclient.client import GraphDatabase
import pep

app = Flask(__name__)
url = "http://133.16.239.120:7474/db/data/"
gdb = GraphDatabase(url)



def conn_f():
    _conn = mysql.connector.connect(host='133.16.239.118',port=3306, user='gui', passwd='test', db='sample_app', charset='utf8')
    return _conn


def _is_account_valid(input_email, input_password):
    # データベース処理でエラー対応をするためのtryとexcept
    try:
        #データベースの情報
        conn = conn_f()
        cursor = conn.cursor()
        mysql_cmd = 'select password from users where email="{0}";'.format(input_email)
        cursor.execute(mysql_cmd)
        pwd = cursor.fetchone()

        # データベースとの接続を切ります。
        cursor.close()
        conn.close()

        # パスワードがあっていれば、trueを返します
        if check_password_hash(pwd[0], input_password):
            print("ログイン成功")
            return True
        else:
            return False
    except:
        print("エラーです")
        return False


# 登録後のページの表示
@app.route('/')
def index():
    if 'user_id' in session:
        username = session['username']
        # ユーザIDをキーとして、ユーザが在籍していた学校とその在籍年度を取得する
        query = "MATCH(n:Person{{id:'{}'}})-[rel:belong]->(class)-[in]->(school) RETURN school, rel"
        results = gdb.query(query.format(username),data_contents=True)
        dic = []
        for i in range(len(results)):
            results[i][0]['data'].update(results[i][1]['data'])
            dic.append(results[i][0]['data'])
            if dic[i]['year'] == 2020:
                belong_school =dic[i]
        return render_template('index.html',link_name=belong_school['name'],school_id=belong_school['id'],type='school')
    return redirect('/login') # ログイン処理は次のテキストで実装します。


@app.route('/<sch_id>')
def school(sch_id):
    if 'user_id' in session:
        username = session['username']
        # ユーザIDと学校IDをキーとして、ユーザが担任または指導していたクラスとその年度を取得する
        query = "MATCH(n:Person{{id:'{}'}})-[rel:belong]->(class)-[:in]->(m:School{{id:'{}'}})RETURN class,rel"
        results = gdb.query(query.format(username,sch_id),data_contents=True)
        dic = []
        for i in range(len(results)):
            results[i][0]['data'].update(results[i][1]['data'])
            dic.append(results[i][0]['data'])
            if dic[i]['year'] == 2020:
                belong_class =dic[i]
        return render_template("index2.html",link_name=belong_class['name'],school_id=sch_id, class_id=belong_class['id'],year=belong_class['year'],type='classes')
    return redirect('/login')


@app.route('/<sch_id>/<cls_id>/<bel_year>')
def classes(sch_id,cls_id,bel_year):
    if 'user_id' in session:
        query = "MATCH (n:Student)-[:belong{{year:{}}}]->(:Class{{id:'{}'}}) RETURN n;"
        results = gdb.query(query.format(bel_year,cls_id),data_contents=True)
        dic = []
        for i in results:
            dic.append(i[0]['data'])
        return render_template('index3.html',list=dic,school_id=sch_id,class_id=cls_id,year=bel_year,type='students')
    return redirect('/login')


@app.route('/<sch_id>/<cls_id>/<bel_year>/<std_id>/')
def students(sch_id,cls_id,bel_year,std_id):
    if 'user_id' in session:
        if pep._confirm_server_alive(std_id):
            return render_template('hello_world.html',message='success')
        return render_template('hello_world.html',message='failed')
    return redirect('/login')


@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        input_pass = request.form['password']

        hash_pass = generate_password_hash(input_pass) 
        date = datetime.now().strftime("%Y/%m/%d %H:%M:%S")


        # データベースにデータを入れる
        conn = conn_f()
        cursor = conn.cursor()
        mysql_cmd = 'insert into users(username, email, password, date_time) values("{0}", "{1}", "{2}", "{3}");'.format(username,
                                  email,
                                  hash_pass,
                                  date)
        cursor.execute(mysql_cmd)
        conn.commit()

        # user_idを取得
        cursor.close()
        conn.close()  

        # session保持
        session['user_id'] = cursor.lastrowid
        return redirect('/')

    return render_template('sign_up.html')


# ログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
  #入力内容が正しければindex()に移ります。
  if request.method == 'POST':
    if _is_account_valid(request.form['email'],request.form['password']):
        conn = conn_f()
        cursor = conn.cursor()
        mysql_cmd = 'select user_id, username from users where email= "{0}";'.format(request.form['email'])
        cursor.execute(mysql_cmd)
        user_id = cursor.fetchall()
        (session['user_id'], session['username']) = user_id[0]
        cursor.close()
        conn.close()  

        return redirect('/')
      #正しくなければもう一度loginページを表示します
    else:
        e_mess = "入力内容が間違っています"
        return render_template('login.html', message=e_mess)
  # 一番最初にページを開いた時の処理
  return render_template('login.html')

# ログアウト機能
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect('/login')


# sessionの暗号化を実施
app.secret_key = 'Zr9A 0/8j3yX!jmN]LWX/,?RTR~XHH'

if __name__ == "__main__":
    app.run(port = 8000, host='0.0.0.0', debug=True)
