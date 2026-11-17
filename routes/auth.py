from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from extensions import db
from forms import HeroForm, LoginForm, SignupForm
from models import User
from services.progress import ensure_progress

auth_bp = Blueprint('auth', __name__)

def find_user_by_email(email):
    return db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        if find_user_by_email(email):
            flash('That email is already registered.', 'error')
            return render_template('signup.html', form=form)

        user = User(
            name=form.name.data.strip(),
            email=email,
            hero_name=form.name.data.strip()[:20],
            avatar_id="1"
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('That email is already registered.', 'error')
            return render_template('signup.html', form=form)
        
        ensure_progress(user)
        login_user(user)
        flash('Account created. Choose your hero!', 'success')
        return redirect(url_for('auth.hero'))

        login_user(user)
        flash('Account created. Choose your hero!', 'success')
        return redirect(url_for('auth.hero'))

    return render_template('signup.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = find_user_by_email(form.email.data.strip().lower())
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.home'))
        flash('Wrong email or password.', 'error')

    return render_template('login.html', form=form)

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))

@auth_bp.route('/hero', methods=['GET', 'POST'])
@login_required
def hero():
    form = HeroForm()
    if request.method == 'GET':
        form.hero_name.data = current_user.hero_name
        form.avatar_id.data = str(current_user.avatar_id)

    if form.validate_on_submit():
        current_user.hero_name = form.hero_name.data.strip()
        current_user.avatar_id = str(form.avatar_id.data)
        db.session.commit()
        flash('Hero saved.', 'success')
        return redirect(url_for('main.home'))

    return render_template('hero.html', form=form)