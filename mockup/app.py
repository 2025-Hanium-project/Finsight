from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/dday')
def dday():
    return render_template('d_day.html')

@app.route('/dplus1')
def dplus1():
    return render_template('d_plus1.html')

@app.route('/detail')
def detail():
    return render_template('detail.html')

@app.route('/mypage')
def mypage():
    return render_template('mypage.html')

@app.route('/signup')
def join():
    return render_template('signup.html')

@app.route('/profile_edit') 
def profile_edit():
    return render_template('profile_edit.html')

@app.route('/findpwd')
def findpwd():
    return render_template('findpwd.html')

if __name__ == '__main__':
    app.run(debug=True)
