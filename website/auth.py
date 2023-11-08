from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from .models import User
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

auth = Blueprint('auth', __name__)

def admin_id_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = current_user
        if not user:
            flash("No tan rapido vaquero.", "danger")
            return redirect(url_for("login"))
        
        expected_user_id = 1  
        if user.id != expected_user_id:
            flash("Nu-uh.", "danger")
            return redirect(url_for("views.home"))

        return f(*args, **kwargs)
    return decorated_function

@auth.route('/login', methods=['GET', 'POST'])
def login():
    nobars=True
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash(f'Bienvenid@, {user.username}!' , category='success')
                return redirect(url_for('views.home'))
            else:
                flash('Contraseña incorrecta.', category='danger')
        else:
            flash('Usuario no existe.', category='danger')

    return render_template("login.html", user=current_user, nobars=nobars)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Te extrañaremos!', category='success')
    return redirect(url_for('views.home'))

@auth.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    nobars = True
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()

        if user:
            flash('El correo electronico ya esta registrado.', category='danger')
        elif len(username) < 3:
            flash('Usuario invalido.', category='danger')
        elif len(email) < 10:
            flash('El correo electronico es invalido.', category='danger')
        elif len(password1) < 4:
            flash('La contraseña debe contener almenos 4 caracteres.', category='danger')
        elif password1 != password2:
            flash('Las contraseñas no coinciden.', category='danger')
        else:
            new_user = User(email=email, username=username, password=generate_password_hash(password1, method='scrypt', salt_length=16))
            db.session.add(new_user)
            db.session.commit()

            user = User.query.filter_by(email=email).first()

            login_user(user, remember=True)
            flash('Cuenta creada exitosamente!', category='success')
            return redirect(url_for('views.home'))
        
    return render_template("sign_up.html", user=current_user, nobars=nobars)

@auth.route('/change_password', methods=['GET', 'POST'])
def change_password():
    nobars = True
    if request.method == 'POST':
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if not email or not password1 or not password2:
            flash('Por favor, complete todos los campos.', 'danger')
            return render_template("change_password.html", nobars=nobars, user=current_user)

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No se encontró ningún usuario con ese correo electrónico.', 'danger')
            return render_template("change_password.html", nobars=nobars, user=current_user)

        if password1 != password2:
            flash('Las contraseñas no coinciden. Inténtalo de nuevo.', 'danger')
            return render_template("change_password.html", nobars=nobars, user=current_user)

        password=generate_password_hash(password1, method='scrypt', salt_length=16)
        user.password = password
        db.session.commit()

        flash('Contraseña cambiada exitosamente. Inicia sesión con tu nueva contraseña.', 'success')
        return redirect(url_for('auth.login'))

    return render_template("change_password.html", nobars=nobars, user=current_user)