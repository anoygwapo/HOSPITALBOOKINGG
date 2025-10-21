from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'hospital_secret_key'

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
db = SQLAlchemy(app)

# -----------------------------
# DATABASE MODELS
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # NEW COLUMN


# -----------------------------
# ROUTES
# -----------------------------

@app.route('/')
def landing():
    return render_template('landing.html')

# -----------------------------
# ADMIN ROUTES
# -----------------------------
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simple static admin credentials (you can replace this later)
        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials', 'danger')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' not in session:
        flash('Please log in as admin first.', 'warning')
        return redirect(url_for('admin_login'))

    appointments = Appointment.query.all()
    return render_template('admin_dashboard.html', appointments=appointments)

@app.route('/approve/<int:id>', methods=['POST'])
def approve_booking(id):
    if 'admin' not in session:
        flash('Please log in as admin first.', 'warning')
        return redirect(url_for('admin_login'))

    appointment = Appointment.query.get_or_404(id)
    appointment.status = 'Approved'
    db.session.commit()
    flash(f'Appointment ID {id} approved!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/decline/<int:id>', methods=['POST'])
def decline_booking(id):
    if 'admin' not in session:
        flash('Please log in as admin first.', 'warning')
        return redirect(url_for('admin_login'))

    appointment = Appointment.query.get_or_404(id)
    appointment.status = 'Declined'
    db.session.commit()
    flash(f'Appointment ID {id} declined!', 'danger')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    flash('Admin logged out successfully.', 'info')
    return redirect(url_for('landing'))

# -----------------------------
# USER ROUTES
# -----------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'warning')
            return redirect(url_for('register'))

        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('book_appointment'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/book', methods=['GET', 'POST'])
def book_appointment():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        time = request.form['time']
        reason = request.form['reason']

        new_appointment = Appointment(
            user_id=session['user_id'],
            name=name,
            date=date,
            time=time,
            reason=reason
        )
        db.session.add(new_appointment)
        db.session.commit()

        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('my_appointments'))

    return render_template('book.html')


@app.route('/cancel/<int:id>')
def cancel_appointment(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    appointment = Appointment.query.get_or_404(id)

    # Ensure user only deletes their own appointment
    if appointment.user_id != session['user_id']:
        flash('You are not authorized to cancel this appointment.')
        return redirect(url_for('my_appointments'))

    db.session.delete(appointment)
    db.session.commit()
    flash('Appointment canceled successfully!')
    return redirect(url_for('my_appointments'))


@app.route('/my_appointments')
def my_appointments():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    appointments = Appointment.query.filter_by(user_id=session['user_id']).all()
    return render_template('my_appointments.html', appointments=appointments)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('landing'))
@app.route('/about')
def about():
    return render_template('about.html')

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
