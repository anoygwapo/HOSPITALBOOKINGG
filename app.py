from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'hospital_secret_key'

# -----------------------------
# DATABASE SETUP
# -----------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///booking.db'
db = SQLAlchemy(app)

# -----------------------------
# DATABASE MODELS
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    contact = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    schedule = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='Available')

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='Pending')

    doctor = db.relationship('Doctor', backref='appointments')

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

        # Static admin credentials
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
    doctors = Doctor.query.all()
    return render_template('admin_dashboard.html', appointments=appointments, doctors=doctors)

@app.route('/doctor_register', methods=['GET', 'POST'])
def register_doctor():
    if 'admin' not in session:
        flash('Please log in as admin first.', 'warning')
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        name = request.form['name']
        specialization = request.form['specialization']
        schedule = request.form['schedule']

        new_doctor = Doctor(
            name=name,
            specialization=specialization,
            schedule=schedule
        )
        db.session.add(new_doctor)
        db.session.commit()

        flash(f'Doctor {name} added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('doctor_register.html')


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
        fullname = request.form['fullname']
        email = request.form['email']
        contact = request.form['contact']
        address = request.form['address']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'warning')
            return redirect(url_for('register'))

        new_user = User(
            fullname=fullname,
            email=email,
            contact=contact,
            address=address,
            password=password
        )
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
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    appointments = Appointment.query.filter_by(user_id=session['user_id']).all()
    doctors = Doctor.query.all()
    return render_template('dashboard.html', user=user, appointments=appointments, doctors=doctors)

@app.route('/book', methods=['GET', 'POST'])
def book_appointment():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    doctors = Doctor.query.all()
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        date = request.form['date']
        time = request.form['time']
        reason = request.form['reason']

        new_appointment = Appointment(
            user_id=user.id,
            doctor_id=doctor_id,
            name=user.fullname,  # Auto-fill user's name
            date=date,
            time=time,
            reason=reason
        )
        db.session.add(new_appointment)
        db.session.commit()

        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('my_appointments'))

    return render_template('book.html', doctors=doctors, user=user)

@app.route('/cancel/<int:id>')
def cancel_appointment(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    appointment = Appointment.query.get_or_404(id)

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
# AUTO-SEED DOCTORS & RUN APP
# -----------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Auto-add sample doctors if none exist
        if not Doctor.query.first():
            doctors = [
                Doctor(name='Dr. Maria Santos', specialization='Pediatrics', schedule='Mon-Fri, 9AM-4PM'),
                Doctor(name='Dr. John Dela Cruz', specialization='Cardiology', schedule='Tue-Thu, 10AM-3PM'),
                Doctor(name='Dr. Ana Reyes', specialization='Dermatology', schedule='Mon-Wed, 8AM-2PM')
            ]
            db.session.add_all(doctors)
            db.session.commit()

    app.run(debug=True)
