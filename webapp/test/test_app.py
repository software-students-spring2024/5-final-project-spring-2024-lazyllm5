import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module='mongomock.__version__')
import pytest
from flask_login import login_user, current_user, logout_user
from webapp.app import app, bcrypt, users, db, User, load_user
from mongomock import MongoClient
from datetime import datetime
from bson import ObjectId

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['LOGIN_DISABLED'] = False
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()
    with app.app_context():
        app.db = MongoClient().db
    yield client

@pytest.fixture
def logged_in_user(client):
    with app.test_request_context():
        with app.app_context():
            users.delete_many({'username': 'testuser'})
            hashed_password = bcrypt.generate_password_hash('testpassword').decode('utf-8')
            test_user_id = ObjectId()
            test_user = {'_id': test_user_id, 'username': 'testuser', 'password': hashed_password}
            users.insert_one(test_user)
            user = User(str(test_user['_id']), test_user['username'])
            login_user(user)
            assert current_user.is_authenticated
        yield user
        with app.app_context():
            logout_user()

def test_login_page(client):
    """ Test login page access """
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data

def test_register_user(client):
    """ Test user registration """
    response = client.post('/register', data={
        'username': 'newuser',
        'password': 'newpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data

def test_login(client, logged_in_user):
    """ Test user login and redirect to home """
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'welcome' in response.data

def test_home_without_login(client):
    """ Test home page without login """
    response = client.get('/')
    assert response.status_code == 302

def test_home_with_login(client, logged_in_user):
    """ Test home page with logged in user """
    response = client.get('/')
    assert response.status_code == 302

def test_logout(client, logged_in_user):
    """ Test logout """
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data

def test_add_transaction(client, logged_in_user):
    """ Test adding a transaction """
    response = client.post('/add-transaction', data={
        'item_name': 'Coffee',
        'amount': '2.50',
        'category': 'Food',
        'date': datetime.now().strftime('%Y-%m-%d')
    }, follow_redirects=True)
    assert response.status_code == 200

def create_transaction_for_test_user(db, user_id):
    """ Helper function to create a transaction for testing. """
    transaction_data = {
        'item_name': 'Test Coffee',
        'amount': 5.00,
        'category': 'Beverages',
        'date': datetime.now().strftime('%Y-%m-%d'),
        'user_id': user_id
    }
    return db.transactions.insert_one(transaction_data).inserted_id

def test_edit_transaction(client, logged_in_user):
    """ Test editing an existing transaction """
    transaction_id = create_transaction_for_test_user(app.db, logged_in_user.id)
    updated_data = {
        'item_name': 'Updated Coffee',
        'amount': 3.00,
        'category': 'Beverages',
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    response = client.post(f'/edit-transaction/{transaction_id}', data=updated_data, follow_redirects=True)
    assert response.status_code == 200

def test_delete_transaction(client, logged_in_user):
    """ Test deleting a transaction """
    transaction_id = create_transaction_for_test_user(app.db, logged_in_user.id)
    response = client.post(f'/delete-transaction/{transaction_id}', follow_redirects=True)
    assert response.status_code == 200

def test_detailed_spending_summary(client, logged_in_user):
    """ Test viewing detailed spending summary """
    response = client.get('/detailed-spending-summary?year=2023&month=1')
    assert response.status_code == 302

def test_spending_summary(client, logged_in_user):
    """ Test overall spending summary """
    response = client.get('/spending-summary')
    assert response.status_code == 302

def mock_transaction_data(db):
    """ Inserts mock data into the MongoDB collection for testing. """
    transactions = db.transactions
    transactions.insert_many([
        {
            'item_name': 'Coffee',
            'amount': 4.50,
            'category': 'Beverages',
            'date': datetime(2023, 1, 10).strftime('%Y-%m-%d'),
            'user_id': 'testuser123'
        },
        {
            'item_name': 'Sandwich',
            'amount': 8.99,
            'category': 'Food',
            'date': datetime(2023, 1, 10).strftime('%Y-%m-%d'),
            'user_id': 'testuser123'
        }
    ])

@pytest.fixture(autouse=True)
def clean_up():
    yield
    with app.app_context():
        db.users.delete_many({})
        db.transactions.delete_many({})

def test_load_user_existing(client, mocker):
    # Mock the MongoDB call
    mock_find_one = mocker.patch('webapp.app.users.find_one')
    mock_find_one.return_value = {'_id': ObjectId('507f191e810c19729de860ea'), 'username': 'testuser'}

    # Load user using the mocked DB return
    from webapp.app import load_user
    user = load_user('507f191e810c19729de860ea')

    assert user is not None
    assert user.username == 'testuser'

def test_load_user_non_existing(client, mocker):
    # Mock the MongoDB call to return None
    mock_find_one = mocker.patch('webapp.app.users.find_one')
    mock_find_one.return_value = None

    # Use a valid ObjectId format but ensure it does not exist in your database
    non_existing_id = '507f1f77bcf86cd799439011'

    # Try to load user with non-existing ID
    from webapp.app import load_user
    user = load_user(non_existing_id)

    assert user is None

