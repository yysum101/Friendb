from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

common_head = '''
<!doctype html>
<html lang="en">
  <head>
    <title>FriendBook</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 20px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
      }
      .container {
        max-width: 700px;
        width: 100%;
        background: white;
        border-radius: 12px;
        padding: 30px 35px;
        box-shadow: 0 8px 25px rgba(0, 150, 136, 0.3);
        margin-bottom: 40px;
      }
      h1, h2, h3 {
        font-weight: 700;
        color: #00796b;
        text-align: center;
        margin-bottom: 20px;
        letter-spacing: 1.2px;
      }
      input, textarea {
        border-radius: 12px !important;
        border: 1.8px solid #009688 !important;
        padding: 14px 18px !important;
        box-shadow: inset 0 2px 6px rgba(0, 150, 136, 0.2);
        font-size: 1.1rem !important;
        transition: border-color 0.3s ease-in-out !important;
      }
      input:focus, textarea:focus {
        outline: none !important;
        border-color: #004d40 !important;
        box-shadow: 0 0 12px rgba(0, 105, 92, 0.7) !important;
      }
      button {
        border-radius: 6px !important;
        background: linear-gradient(135deg, #00796b, #004d40) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        padding: 12px 26px !important;
        box-shadow: 0 7px 20px rgba(0, 150, 136, 0.5);
        transition: background 0.3s ease-in-out !important;
        cursor: pointer;
      }
      button:hover {
        background: linear-gradient(135deg, #004d40, #00796b) !important;
      }
      .btn-secondary {
        background: #00695c !important;
        box-shadow: none !important;
        border-radius: 6px !important;
      }
      .btn-secondary:hover {
        background: #004d40 !important;
      }
      .card {
        border-radius: 16px !important;
        box-shadow: 0 8px 25px rgba(0, 150, 136, 0.2) !important;
        margin-bottom: 24px !important;
        transition: box-shadow 0.3s ease-in-out;
      }
      .card:hover {
        box-shadow: 0 12px 40px rgba(0, 150, 136, 0.35) !important;
      }
      .chat-bubble {
        padding: 18px 26px;
        border-radius: 18px;
        max-width: 72%;
        margin-bottom: 18px;
        word-wrap: break-word;
        box-shadow: 0 5px 20px rgba(0, 150, 136, 0.3);
        font-size: 1.1rem;
        line-height: 1.4;
        position: relative;
        clear: both;
        animation: fadeIn 0.45s ease forwards;
      }
      .chat-left {
        background-color: #d0f0f4;
        text-align: left;
        float: left;
        color: #004d40;
      }
      .chat-right {
        background-color: #00796b;
        text-align: right;
        float: right;
        color: white;
      }
      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
      }
      form.inline {
        display: inline-block;
        margin-left: 12px;
      }
      small {
        font-size: 0.82rem;
        opacity: 0.75;
      }
      .clearfix::after {
        content: "";
        clear: both;
        display: table;
      }
      a {
        color: #004d40;
        text-decoration: none;
        font-weight: 700;
      }
      a:hover {
        text-decoration: underline;
      }
      .flash-message {
        background: #00796b;
        color: white;
        padding: 12px 18px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 9px 28px rgba(0, 150, 136, 0.5);
        text-align: center;
        font-weight: 700;
        letter-spacing: 0.6px;
      }
    </style>
  </head>
  <body>
'''

template_index = common_head + '''
    <div class="container">
      <h1>FriendBook</h1>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          {% for msg in messages %}
            <div class="flash-message">{{ msg }}</div>
          {% endfor %}
        {% endif %}
      {% endwith %}
      <form action="{{ url_for('logout') }}" method="POST" style="float: right;">
        <button class="btn btn-secondary btn-sm">Logout</button>
      </form>
      <a href="{{ url_for('chat') }}" class="btn btn-primary btn-sm mb-3">Chat</a>
      <div style="clear: both;"></div>
      <form method="POST" action="/post">
        <textarea name="content" class="form-control" placeholder="What's on your mind?" required></textarea><br>
        <button type="submit" class="btn btn-success">Post</button>
      </form>
      <hr>
      {% for post in posts %}
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">{{ post.user.username }}</h5>
            <p class="card-text">{{ post.content }}</p>
            <small class="text-muted">{{ post.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</small>
            <hr>
            <form action="/comment/{{ post.id }}" method="POST">
              <input name="content" placeholder="Comment..." class="form-control" required style="border-radius: 12px; padding: 10px;">
              <button class="btn btn-info btn-sm mt-2" style="border-radius: 12px;">Comment</button>
            </form>
            {% for comment in comments if comment.post_id == post.id %}
              <div class="mt-2">
                <strong>{{ comment.user.username }}:</strong> {{ comment.content }}
                <small class="text-muted">({{ comment.timestamp.strftime('%Y-%m-%d %H:%M:%S') }})</small>
                {% if comment.user_id == user.id %}
                  <form action="/edit_comment/{{ comment.id }}" method="POST" class="inline">
                    <input name="content" value="{{ comment.content }}" required style="border-radius: 6px; border: 1px solid #009688; padding: 4px 8px; font-size: 0.9rem;">
                    <button class="btn btn-warning btn-sm" style="border-radius:6px; box-shadow: 0 3px 10px rgba(0, 150, 136, 0.35);">Edit</button>
                  </form>
                  <form action="/delete_comment/{{ comment.id }}" method="POST" class="inline">
                    <button class="btn btn-danger btn-sm" style="border-radius:6px; box-shadow: 0 3px 10px rgba(0, 150, 136, 0.35);">Delete</button>
                  </form>
                {% endif %}
              </div>
            {% endfor %}
          </div>
        </div>
      {% endfor %}
    </div>
  </body>
</html>
'''

template_register = common_head + '''
    <div class="container">
      <h2>Register</h2>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          {% for msg in messages %}
            <div class="flash-message">{{ msg }}</div>
          {% endfor %}
        {% endif %}
      {% endwith %}
      <form method="POST">
        <input name="username" placeholder="Username" class="form-control" required><br>
        <input name="password" type="password" placeholder="Password" class="form-control" required><br>
        <button type="submit" class="btn btn-primary">Register</button>
      </form>
      <p>Already have an account? <a href="/login">Login</a></p>
    </div>
  </body>
</html>
'''

template_login = common_head + '''
    <div class="container">
      <h2>Login</h2>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          {% for msg in messages %}
            <div class="flash-message">{{ msg }}</div>
          {% endfor %}
        {% endif %}
      {% endwith %}
      <form method="POST">
        <input name="username" placeholder="Username" class="form-control" required><br>
        <input name="password" type="password" placeholder="Password" class="form-control" required><br>
        <button type="submit" class="btn btn-success">Login</button>
      </form>
      <p>Don't have an account? <a href="/register">Register</a></p>
    </div>
  </body>
</html>
'''

template_chat = common_head + '''
    <div class="container">
      <h2>Chat Room</h2>
      <form action="{{ url_for('logout') }}" method="POST" style="float: right;">
        <button class="btn btn-secondary btn-sm" style="border-radius:6px;">Logout</button>
      </form>
      <a href="{{ url_for('index') }}" class="btn btn-primary btn-sm mb-3" style="border-radius:6px;">Home</a>
      <div style="clear: both;"></div>
      {% with messages = get_flashed_messages() %}
        {% if messages %}
          {% for msg in messages %}
            <div class="flash-message">{{ msg }}</div>
          {% endfor %}
        {% endif %}
      {% endwith %}

      <!-- Messages display -->
      <div style="max-height: 400px; overflow-y: auto; margin-bottom: 15px;">
        {% for msg in messages %}
          <div class="chat-bubble {% if msg.user_id == user.id %}chat-right{% else %}chat-left{% endif %}">
            <small><strong>{{ msg.user.username }}</strong> - {{ msg.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</small><br>
            {{ msg.content }}
          </div>
        {% endfor %}
      </div>

      <!-- Input form below -->
      <form method="POST">
        <textarea name="content" class="form-control" placeholder="Type a message..." required style="border-radius:12px; resize:none; height:80px;"></textarea><br>
        <button type="submit" class="btn btn-info" style="border-radius:12px; width: 100%;">Send</button>
      </form>
    </div>
  </body>
</html>
'''

@app.route('/')
@login_required
def index():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    comments = Comment.query.all()
    return render_template_string(template_index, user=current_user, posts=posts, comments=comments)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. Please login.")
        return redirect(url_for('login'))
    return render_template_string(template_register)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        flash("Invalid credentials")
    return render_template_string(template_login)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/post', methods=['POST'])
@login_required
def create_post():
    content = request.form['content']
    new_post = Post(user_id=current_user.id, content=content)
    db.session.add(new_post)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment(post_id):
    content = request.form['content']
    new_comment = Comment(user_id=current_user.id, post_id=post_id, content=content)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/edit_comment/<int:comment_id>', methods=['POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment and comment.user_id == current_user.id:
        comment.content = request.form['content']
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment and comment.user_id == current_user.id:
        db.session.delete(comment)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'POST':
        content = request.form['content']
        new_message = ChatMessage(user_id=current_user.id, content=content)
        db.session.add(new_message)
        db.session.commit()
        return redirect(url_for('chat'))
    messages = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).all()
    return render_template_string(template_chat, user=current_user, messages=messages)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
