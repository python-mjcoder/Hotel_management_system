from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key' 

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:mangesh2345@localhost/hotel_db"
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel_db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = 'your_secret_key'

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def check_password(self, password):
        return check_password_hash(self.password, password)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    room_count = db.Column(db.Integer, nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()
        print("Admin login POST request received.")

        if admin and admin.check_password(password):
            session['admin_logged_in'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')



@app.route('/')
def index():
    return redirect(url_for('register'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not username or not password:
            flash('All fields are required')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful!')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin if isinstance(user.is_admin, bool) else False
            flash('Login successful!')
            return redirect(url_for('home'))  # Redirect to home after login
        else:
            flash('Invalid credentials!', 'danger')

    return render_template('login.html')


@app.route('/home')
def home():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin first.', 'warning')
        return redirect(url_for('admin_login'))

    bookings = Booking.query.all()
    return render_template('admin_dashboard.html', bookings=bookings)


@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            city = request.form['city']
            room_type = request.form['room_type']
            room_count = int(request.form['room_count'])
            check_in = datetime.strptime(request.form['check_in'], '%Y-%m-%d').date()
            check_out = datetime.strptime(request.form['check_out'], '%Y-%m-%d').date()

            
            if check_in >= check_out:
                flash('Check-out date must be after check-in date.', 'danger')
                return redirect(url_for('booking'))
            
            price_per_night = {
                'Single': 1000,
                'Double': 1800,
                'Suite': 3000
            }
            nights = (check_out - check_in).days
            price = nights * room_count * price_per_night.get(room_type, 1000)


            booking = Booking(
                name=name,
                email=email,
                city=city,
                room_type=room_type,
                room_count=room_count,
                check_in_date=check_in,
                check_out_date=check_out,
                price=price
            )
            db.session.add(booking)
            db.session.commit()
            flash('Your booking was successful!', 'success')
            return redirect(url_for('home'))  

        except Exception as e:
            db.session.rollback()
            flash(f'Error occurred: {e}', 'danger')
            return redirect(url_for('booking'))

    return render_template('booking.html')


if __name__ == '__main__':
    with app.app_context():
        from werkzeug.security import generate_password_hash

        
        if not Admin.query.filter_by(username="admin").first():
            hashed_pw = generate_password_hash("admin123")
            new_admin = Admin(username="admin", password=hashed_pw)
            db.session.add(new_admin)
            db.session.commit()
            print("Admin created.")
        else:
            print("Admin already exists.")

    app.run(debug=True)
