# views.py

from flask import render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

from app import app
from app.data import Articles

Articles = Articles()

app.secret_key='secrect123'

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Autonoma123*'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#INIT MYSQL
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/articles')
def articles():
	return render_template('articles.html', articles = Articles)

@app.route('/article/<string:id>')
def article(id):
	return render_template('article.html', id=id)

class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message='Password do not match')
		])
	confirm = PasswordField('Confirm Password')

class RegisterForm2(Form):
    title = StringField('Title', [validators.Length(min=1, max=100)])
    author = StringField('Author', [validators.Length(min=1, max=100)])
    created_date = StringField('Created Date', [validators.Length(min=1, max=20)])

@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		# Create Cursor
		cur = mysql.connection.cursor()
	
		# Execute Query
		cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username,password))

		# Commit to DB
		mysql.connection.commit()

		# Close connection
		cur.close()

		flash('You are now registered and can log in', 'success')

		return redirect(url_for('index'))
	
	return render_template('register.html', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
	
		# Get Form Fields
		username = request.form['username']
		password_candidate = request.form['password']

		# Create cursor
		cur = mysql.connection.cursor()

		# Get user by username	
		result = cur.execute("SELECT * FROM users WHERE username =%s",[username])

		if result > 0:
			# Get stored hash
			data = cur.fetchone()
			password = data['password']

			# Compare Passwords
			if sha256_crypt.verify(password_candidate, password):
				# Passed
				session['logged_in'] = True
				session['username'] = username
				flash('You are logged in', 'success')
				app.logger.info('PASSWORD MATCHED')
				return redirect(url_for('dashboard'))		
	
			else:
				app.logger.info('PASSWORD NO MATCHED')
				error = 'Invalid login'
				return render_template('login.html', error=error)
		
			# Close connection
			cur.close()

		else:
			app.logger.info('NO USER')
			error = 'Username not found'
			return render_template('login.html', error=error)
			

	return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Plese login', 'danger')
			return redirect(url_for('login'))
	return wrap

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT id, title, author, created_date FROM articles")
    articles = cur.fetchall()
    cur.close()  # Es importante cerrar el cursor después de usarlo

    return render_template('dashboard.html', articles=articles)


@app.route('/add_article', methods=['GET', 'POST'])
def add_article():
	form = RegisterForm2(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		author = form.author.data
		created_date = form.created_date.data

		# Create Cursor
		cur = mysql.connection.cursor()
	
		# Execute Query
		cur.execute("INSERT INTO articles(title, author, created_date) VALUES(%s, %s, %s)", (title, author,created_date))

		# Commit to DB
		mysql.connection.commit()

		# Close connection
		cur.close()

		flash('Your article was added with successfully', 'success')

		return redirect(url_for('dashboard'))
	
	return render_template('add_article.html', form=form)

@app.route('/edit_article/<int:id>', methods=['GET', 'POST'])
def edit_article(id):
    # Obtener el artículo de la base de datos usando el ID
    #cur = mysql.connection.cursor()
    #cur.execute("SELECT * FROM articles WHERE id = %s", (id,))
    #article = cur.fetchone()
    #cur.close()

    # Llenar el formulario con los datos del artículo
    form = RegisterForm2(request.form)
  #  form.title.data = article['title']
 #   form.author.data = article['author']
#    form.created_date.data = article['created_date']

    if request.method == 'POST' and form.validate():
        # Obtener los datos del formulario y actualizar el artículo en la base de datos
        title = form.title.data
        author = form.author.data
        created_date = form.created_date.data

        cur = mysql.connection.cursor()

        try:
            cur.execute("UPDATE articles SET title=%s, author=%s, created_date=%s WHERE id=%s", (title, author, created_date, id))
            mysql.connection.commit()
            flash('Your article was updated successfully', 'success')
        except Exception as e:
            mysql.connection.rollback()  # Revertir cambios en caso de error
            flash('Failed to update the article', 'error')
            print("Error:", e)
        finally:
            cur.close()


        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

@app.route('/delete_article/<int:id>', methods=['POST'])
def delete_article(id):
        # Crear cursor
    cur = mysql.connection.cursor()

    try:
        # Ejecutar la consulta para eliminar el artículo
        cur.execute("DELETE FROM articles WHERE id = %s", (id,))
        
        # Confirmar la transacción
        mysql.connection.commit()

        flash('Article deleted successfully', 'success')

    except Exception as e:
        # Si hay un error, revertir la transacción
        mysql.connection.rollback()
        flash('Error deleting article: ' + str(e), 'error')

    finally:
        # Cerrar la conexión
        cur.close()

    # Redirigir de vuelta a la página de dashboard
    return redirect(url_for('dashboard'))

# Logout
@app.route('/logout')
def logout():
	session.clear()
	flash('You are now logged out','success')
	return redirect(url_for('login'))	
