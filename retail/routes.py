from flask import render_template, url_for, flash, redirect, request
from retail import app, db, bcrypt
from retail.forms import RegistrationForm, LoginForm
from retail.models import User
from flask_login import login_user, current_user, logout_user, login_required

import sqlite3 

@app.route("/")
@app.route("/home")
def home():
	return render_template('home.html')


@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/women")
def women():
    conn = sqlite3.connect('clothing.db')
    c = conn.cursor()
    c.execute('SELECT * FROM clothing WHERE gender == "Female"')
    items = c.fetchall()
    return render_template('women.html', items=items)

@app.route("/men")
def men():
	conn = sqlite3.connect('clothing.db')
	c = conn.cursor()
	c.execute('SELECT * FROM clothing WHERE gender == "Male"')
	items = c.fetchall()
	return render_template('men.html', items=items)

@app.route("/clothing2")
def clothing2():
    return render_template('clothing2.html')

@app.route("/clothing1")
def clothing1():
    return render_template('clothing1.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(username=form.username.data, email=form.email.data, password=hashed_password)
		db.session.add(user)
		db.session.commit()
		flash('Your account has been created!', 'success')
		return redirect(url_for('login'))
	return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('home'))
		else:
			flash('Login unsuccessful. Please check email and password', 'danger')
	return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('home'))

@app.route("/account")
@login_required #require login first
def account():
	return render_template('account.html', title='Account')

@app.route("/manager")
def manager():
	conn = sqlite3.connect('clothing.db')
	c = conn.cursor()
	c.execute('SELECT * FROM purchase')
	orders = c.fetchall()
	return render_template('manager.html', orders=orders)

@app.route("/cart")
def cart():
	return render_template('cart.html')

@app.route("/clothing/<item_id>")
def shirt(item_id):
    """Function for Individual Shirt Page"""
    conn = sqlite3.connect('clothing.db')
    c = conn.cursor()
    c.execute('SELECT * FROM clothing WHERE cid==%s' % item_id)
    item = c.fetchone()
#    my_item = ""
#    for item in items:
 #       if item["cid"] == item_id:
 #           my_item = item
    return render_template("clothing.html", item=item)

