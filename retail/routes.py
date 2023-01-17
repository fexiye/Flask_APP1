from flask import render_template, url_for, flash, redirect, request
from retail import app, db, bcrypt
from retail.forms import RegistrationForm, LoginForm
from retail.models import User
from flask_login import login_user, current_user, logout_user, login_required

import sqlite3, random

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

@app.route("/manager/checkout")
def managerc():
	conn = sqlite3.connect('clothing.db')
	c = conn.cursor()
	c.execute('SELECT * FROM purchase')
	orders = c.fetchall()
	return render_template('manager.html', orders=orders)

@app.route("/manager/fittingroom")
def managerf():
	conn = sqlite3.connect('clothing.db')
	c = conn.cursor()
	c.execute('SELECT * FROM fittingroom')
	fitting = c.fetchall()
	return render_template('manager.html', fitting=fitting)

@app.route("/removeFromManagerc")
@login_required
def removeFromManagerc():
	Pid = int(request.args.get('pid'))
	with sqlite3.connect('clothing.db') as conn:
		cur = conn.cursor()
		try:
			cur.execute("DELETE FROM purchase WHERE purchaseid = " + str(Pid))
			msg = "removed successfully"
		except:
			conn.rollback()
			msg = "error occured"
	conn.close()
	return redirect(url_for('managerc'))

@app.route("/removeFromManagerf")
@login_required
def removeFromManagerf():
	Pid = int(request.args.get('pid'))
	with sqlite3.connect('clothing.db') as conn:
		cur = conn.cursor()
		try:
			cur.execute("DELETE FROM fittingroom WHERE fittingid = " + str(Pid))
			msg = "removed successfully"
		except:
			conn.rollback()
			msg = "error occured"
	conn.close()
	return redirect(url_for('managerf'))

@app.route("/addToCart", methods = ['POST', 'GET'])
@login_required
def addToCart():
	clothingid = int(request.args.get('cid'))
	si=request.form['size']
	print(si)
	with sqlite3.connect('clothing.db') as conn:
		cur = conn.cursor()
		cur.execute("SELECT id FROM user WHERE email = '" + current_user.email + "'")
		userId = cur.fetchone()[0]
		print(clothingid)
		try:
			cur.execute("INSERT INTO cart (id, cid, size) VALUES (?, ?, ?)", (userId, clothingid, si))
			conn.commit()
			msg = "Added successfully"
		except:
			conn.rollback()
			msg = "Error occured"
	conn.close()
	return redirect(url_for('cart'))

@app.route("/cart")
@login_required
def cart():
	with sqlite3.connect('clothing.db') as conn:
		cur = conn.cursor()
		cur.execute("SELECT id FROM user WHERE email = '" + current_user.email + "'")
		userId = cur.fetchone()[0]
		cur.execute("SELECT clothing.cid, clothing.clothingname, clothing.price, clothing.gender, cart.size, cart.cartnum FROM clothing Inner Join cart On clothing.cid = cart.cid Where cart.id = " + str(userId))
		clothings = cur.fetchall()
	totalPrice = 0
	for row in clothings:
		totalPrice += row[2]
	return render_template("cart.html", clothings = clothings, totalPrice=totalPrice, userId=userId)

@app.route("/removeFromCart")
@login_required
def removeFromCart():
	cartid = int(request.args.get('cid'))
	with sqlite3.connect('clothing.db') as conn:
		cur = conn.cursor()
		cur.execute("SELECT id FROM user WHERE email = '" + current_user.email + "'")
		userId = cur.fetchone()[0]
		try:
			cur.execute("DELETE FROM cart WHERE id = " + str(userId) + " AND cartnum = " + str(cartid))
			conn.commit()
			msg = "removed successfully"
		except:
			conn.rollback()
			msg = "error occured"
	conn.close()
	return redirect(url_for('cart'))

@app.route("/addToCheckout")
@login_required
def addToCheckout():
	with sqlite3.connect('clothing.db') as conn:
		cur = conn.cursor()
		cur.execute('SELECT id FROM user WHERE email = '" + current_user.email + "'')
		userId = cur.fetchone()[0]
		cur.execute('SELECT username FROM user WHERE email = '" + current_user.email + "'')
		user,= cur.fetchone()
		cur.execute('SELECT cid, size FROM cart WHERE id =' + str(userId))
		clothingids =cur.fetchall()
		print(clothingids)
		print(user)
		for x, y, in clothingids:
			print(x,y)
			try:
				cur.execute("INSERT INTO purchase (id, cid, username, size) VALUES (?, ?, ?, ?)", (userId, x, user, y))
				conn.commit()
				cur.execute("DELETE FROM cart WHERE id = " + str(userId))
				conn.commit()
				msg = "Added successfully"
			except:
				conn.rollback()
				msg = "Error occured"
			print(msg)
	conn.close()
	return redirect(url_for('checkout'))

@app.route("/addToFittingroom")
@login_required
def addToFittingroom():
	with sqlite3.connect('clothing.db') as conn:
		cur = conn.cursor()
		cur.execute('SELECT id FROM user WHERE email = '" + current_user.email + "'')
		userId = cur.fetchone()[0]
		cur.execute('SELECT username FROM user WHERE email = '" + current_user.email + "'')
		user,= cur.fetchone()
		cur.execute('SELECT cid, size FROM cart WHERE id =' + str(userId))
		clothingids =cur.fetchall()
		print(clothingids)
		for x, y, in clothingids:
			print(x,y)
			try:
				cur.execute("INSERT INTO fittingroom (id, cid, username, size) VALUES (?, ?, ?, ?)", (userId, x, user, y))
				conn.commit()
				cur.execute("DELETE FROM cart WHERE id = " + str(userId))
				conn.commit()
				msg = "Added successfully"
			except:
				conn.rollback()
				msg = "Error occured"
			print(msg)
	conn.close()
	return redirect(url_for('checkout'))

@app.route("/checkout")
def checkout():
	return render_template('checkout.html')

@app.route("/clothing/<item_id>")
@login_required
def clothing(item_id):
	conn = sqlite3.connect('clothing.db')
	c = conn.cursor()
	c.execute('SELECT * FROM clothing WHERE cid==%s' % item_id)
	item = c.fetchone()
	"""recommendation by category"""
	c.execute('SELECT category1 FROM clothing INNER JOIN recommendation ON clothing.category=recommendation.category WHERE clothing.cid =%s' % item_id)
	cate1 = c.fetchone()
	c.execute('SELECT * FROM clothing WHERE gender = (SELECT gender from clothing where cid= %s) AND category = (SELECT category1 FROM clothing INNER JOIN recommendation ON clothing.category=recommendation.category WHERE clothing.cid = %s)' % (item_id,item_id))
	item1 = random.choice(c.fetchall())
	c.execute('SELECT category2 FROM clothing INNER JOIN recommendation ON clothing.category=recommendation.category WHERE clothing.cid =%s' % item_id)
	cate2 = c.fetchone()
	c.execute('SELECT * FROM clothing WHERE gender = (SELECT gender from clothing where cid= %s) AND category = (SELECT category2 FROM clothing INNER JOIN recommendation ON clothing.category=recommendation.category WHERE clothing.cid = %s)' % (item_id,item_id))
	item2 = random.choice(c.fetchall())
	c.execute('SELECT category3 FROM clothing INNER JOIN recommendation ON clothing.category=recommendation.category WHERE clothing.cid =%s' % item_id)
	cate3 = c.fetchone()
	c.execute('SELECT * FROM clothing WHERE gender = (SELECT gender from clothing where cid= %s) AND category = (SELECT category3 FROM clothing INNER JOIN recommendation ON clothing.category=recommendation.category WHERE clothing.cid = %s)' % (item_id,item_id))
	item3 = random.choice(c.fetchall())
	"""recommendation by category"""

	return render_template("clothing.html", item=item, cate1=cate1, cate2=cate2, cate3=cate3, item1=item1, item2=item2, item3=item3)

