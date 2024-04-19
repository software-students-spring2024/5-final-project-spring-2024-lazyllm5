from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from pymongo import MongoClient, DESCENDING
from bson.objectid import ObjectId
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'a_very_secret_fallback_key')

# MongoDB setup
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)
db = client['BudgetTracker']
users = db.users
transactions = db.transactions

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Flask-Bcrypt setup
bcrypt = Bcrypt(app)

class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = str(user_id)
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    user = users.find_one({"_id": ObjectId(user_id)})
    if user:
        return User(str(user['_id']), user['username'])
    return None

@app.route('/')
@login_required
def home():
    user_transactions = transactions.find({'user_id': current_user.id})
    return render_template('home.html', transactions=list(user_transactions))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.find_one({"username": username})
        if user and bcrypt.check_password_hash(user['password'], password):
            user_obj = User(str(user['_id']), username)
            login_user(user_obj)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_exists = users.find_one({"username": username})
        if user_exists:
            flash('Username already exists')
            return redirect(url_for('register'))
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users.insert_one({"username": username, "password": hashed_password})
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add-transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        date = request.form['date']
        transactions.insert_one({
            'amount': amount,
            'category': category,
            'date': date,
            'user_id': current_user.id
        })
        return redirect(url_for('home'))
    return render_template('add_transaction.html')

@app.route('/edit-transaction/<transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = transactions.find_one({'_id': ObjectId(transaction_id), 'user_id': current_user.id})
    if request.method == 'POST':
        updated_transaction = {
            'amount': float(request.form['amount']),
            'category': request.form['category'],
            'date': request.form['date']
        }
        transactions.update_one({'_id': ObjectId(transaction_id)}, {'$set': updated_transaction})
        return redirect(url_for('home'))
    return render_template('edit_transaction.html', transaction=transaction)

@app.route('/delete-transaction/<transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    transactions.delete_one({'_id': ObjectId(transaction_id), 'user_id': current_user.id})
    flash('Transaction deleted successfully.')
    return redirect(url_for('home'))

@app.route('/detailed-spending-summary')
@login_required
def detailed_spending_summary():
    # Define the pipeline for weekly aggregation
    weekly_pipeline = [
        {'$match': {'user_id': current_user.id}},
        {'$group': {
            '_id': {
                'year': {'$year': {'$toDate': '$date'}},
                'week': {'$week': {'$toDate': '$date'}}
            },
            'total': {'$sum': '$amount'}
        }},
        {'$sort': {'_id.year': -1, '_id.week': -1}}
    ]

    # Define the pipeline for monthly aggregation
    monthly_pipeline = [
        {'$match': {'user_id': current_user.id}},
        {'$group': {
            '_id': {
                'year': {'$year': {'$toDate': '$date'}},
                'month': {'$month': {'$toDate': '$date'}}
            },
            'total': {'$sum': '$amount'}
        }},
        {'$sort': {'_id.year': -1, '_id.month': -1}}
    ]

    # Define the pipeline for yearly aggregation
    yearly_pipeline = [
        {'$match': {'user_id': current_user.id}},
        {'$group': {
            '_id': {
                'year': {'$year': {'$toDate': '$date'}}
            },
            'total': {'$sum': '$amount'}
        }},
        {'$sort': {'_id.year': -1}}
    ]

    # Execute the aggregation queries
    db = client['BudgetTracker']  # assuming 'client' and 'db' are defined and connected elsewhere in your code
    weekly_spending = list(db.transactions.aggregate(weekly_pipeline))
    monthly_spending = list(db.transactions.aggregate(monthly_pipeline))
    yearly_spending = list(db.transactions.aggregate(yearly_pipeline))

    return render_template('detailed_spending_summary.html',
                           weekly_spending=weekly_spending,
                           monthly_spending=monthly_spending,
                           yearly_spending=yearly_spending)

@app.route('/spending-summary')
@login_required
def spending_summary():
    now = datetime.now()
    start_of_week = now - timedelta(days=now.weekday())
    start_of_month = datetime(now.year, now.month, 1)
    start_of_year = datetime(now.year, 1, 1)

    weekly_spending = transactions.aggregate([
        {'$match': {
            'user_id': current_user.id,
            'date': {'$gte': start_of_week.strftime('%Y-%m-%d')}
        }},
        {'$group': {
            '_id': None,
            'total': {'$sum': '$amount'}
        }}
    ])

    monthly_spending = transactions.aggregate([
        {'$match': {
            'user_id': current_user.id,
            'date': {'$gte': start_of_month.strftime('%Y-%m-%d')}
        }},
        {'$group': {
            '_id': None,
            'total': {'$sum': '$amount'}
        }}
    ])

    yearly_spending = transactions.aggregate([
        {'$match': {
            'user_id': current_user.id,
            'date': {'$gte': start_of_year.strftime('%Y-%m-%d')}
        }},
        {'$group': {
            '_id': None,
            'total': {'$sum': '$amount'}
        }}
    ])

    total_spending = transactions.aggregate([
        {'$match': {
            'user_id': current_user.id
        }},
        {'$group': {
            '_id': None,
            'total': {'$sum': '$amount'}
        }}
    ])

    weekly_total = 0
    monthly_total = 0
    yearly_total = 0
    total = 0

    # Safely extract totals
    try:
        weekly_total = next(weekly_spending, {}).get('total', 0)
        monthly_total = next(monthly_spending, {}).get('total', 0)
        yearly_total = next(yearly_spending, {}).get('total', 0)
        total = next(total_spending, {}).get('total', 0)
    except StopIteration:
        pass  # Optionally handle no data case here

    return render_template('spending_summary.html', weekly=weekly_total, monthly=monthly_total, yearly=yearly_total, total=total)


if __name__ == '__main__':
    app.run(debug=True)
