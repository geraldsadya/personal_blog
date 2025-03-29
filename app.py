from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import json
import uuid
from datetime import datetime
import markdown

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

# Ensure data directories exist
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
ARTICLES_DIR = os.path.join(DATA_DIR, 'articles')
if not os.path.exists(ARTICLES_DIR):
    os.makedirs(ARTICLES_DIR)
print(f"Articles will be stored in: {ARTICLES_DIR}")


# Admin credentials (in a real app, use proper authentication)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

# Helper functions for article management
def get_articles():
    articles = []
    for filename in os.listdir(ARTICLES_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(ARTICLES_DIR, filename), 'r') as f:
                article = json.load(f)
                articles.append(article)
    # Sort articles by date (newest first)
    return sorted(articles, key=lambda x: x['date'], reverse=True)

def get_article(article_id):
    file_path = os.path.join(ARTICLES_DIR, f"{article_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def save_article(article):
    if 'id' not in article or not article['id']:
        article['id'] = str(uuid.uuid4())
    
    file_path = os.path.join(ARTICLES_DIR, f"{article['id']}.json")
    with open(file_path, 'w') as f:
        json.dump(article, f, indent=2)
    return article

def delete_article(article_id):
    file_path = os.path.join(ARTICLES_DIR, f"{article_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

# Routes for guest section
@app.route('/')
def home():
    try:
        articles = get_articles()
        return render_template('home.html', articles=articles)
    except Exception as e:
        # Print the error and return a simple text response for debugging
        print(f"Error rendering home page: {e}")
        return f"Error rendering home page: {e}"

@app.route('/article/<article_id>')
def article(article_id):
    article = get_article(article_id)
    if article:
        # Convert markdown content to HTML
        article['content_html'] = markdown.markdown(article['content'])
        return render_template('article.html', article=article)
    return render_template('404.html'), 404

# Authentication routes
@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Admin routes (protected)
@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        try:
            return render_template('admin/login.html')
        except Exception as e:
            print(f"Error rendering login page: {e}")
            return f"Error rendering login page: {e}"
    
    try:
        articles = get_articles()
        return render_template('admin/dashboard.html', articles=articles)
    except Exception as e:
        print(f"Error rendering dashboard: {e}")
        return f"Error rendering dashboard: {e}"

@app.route('/admin/add', methods=['GET', 'POST'])
def add_article():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        article = {
            'title': request.form.get('title'),
            'content': request.form.get('content'),
            'date': request.form.get('date') or datetime.now().strftime('%Y-%m-%d')
        }
        save_article(article)
        flash('Article added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add.html')

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/admin/edit/<article_id>', methods=['GET', 'POST'])
def edit_article(article_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    article = get_article(article_id)
    if not article:
        flash('Article not found!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        article['title'] = request.form.get('title')
        article['content'] = request.form.get('content')
        article['date'] = request.form.get('date')
        save_article(article)
        flash('Article updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit.html', article=article)

@app.route('/admin/delete/<article_id>')
def delete_article_route(article_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if delete_article(article_id):
        flash('Article deleted successfully!', 'success')
    else:
        flash('Article not found!', 'error')
    
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)