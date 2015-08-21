import sys
import flask
from flask import Flask, render_template, request, redirect, url_for, current_app, abort, jsonify
from flask.ext.login import LoginManager, login_required, login_user, logout_user, current_user
from flask.ext.principal import Principal, Permission, RoleNeed, UserNeed, PermissionDenied
from flask.ext.principal import Identity, AnonymousIdentity, identity_changed, identity_loaded
import requests
from functools import wraps

app = Flask(__name__)
app.config["SECRET_KEY"] = "123123123"


facebook_config = {
	'app_id': "", 
	'app_secret': "", 
	'redirect_uri': "" 
}

if len(facebook_config['app_id']) == 0:
    print "app_id empty"
	sys.exit(0)

login_manager = LoginManager()
login_manager.init_app(app)

# load the extension
principals = Principal(app)

# Create a permission with a single Need, in this case a RoleNeed.
admin_permission = Permission(RoleNeed('admin'))
user_permission = Permission(RoleNeed('user'))

@app.errorhandler(PermissionDenied)
def handle_invalid_usage(error):
	response = jsonify(error.to_dict())
	response.status_code = error.status_code
	return response

def requires_roles(*roles):
	def wrapper(f):
		@wraps(f)
		def wrapped(*args, **kwargs):
			if hasattr(current_user, 'roles'):
				for role in current_user.roles:
					if role.name in roles:
						return f(*args, **kwargs)
			return abort(401)
		return wrapped
	return wrapper

@app.route('/')
def index():
	return render_template('index.html', 
							facebook_app_id=facebook_config['app_id'], 
							facebook_redirect_uri=facebook_config['redirect_uri'])

@app.route('/contact')
def contact():
	return render_template('contact.html')

@app.route('/admin')
@admin_permission.require(401)
def admin():
	return render_template('admin.html')

@app.route('/user')
@user_permission.require(401)
def user():
	return render_template('user.html')

@app.route('/useradmin')
@requires_roles('user', 'admin')
def useradmin():
	return render_template('useradmin.html')

@app.route('/facebook')
def facebook():
	code_param = request.args.get('code', '')

	url = "https://graph.facebook.com/v2.3/oauth/access_token?"

	params = "client_id=" + facebook_config['app_id'] + "&redirect_uri=" + facebook_config['redirect_uri'] + "&client_secret=" + facebook_config['app_secret'] + "&code="+ code_param

	r = requests.get(url + params)
	json = r.json()

	r = requests.get('https://graph.facebook.com/v2.3/me?access_token=' + json['access_token'])
	me = r.json()

	#todo - find in database, else create
	user = User(me['first_name'], me['name'], [Role('user')])
	login_user(user)
	
	next = flask.request.args.get('next')

	return flask.redirect(next or flask.url_for('index'))

@app.route('/login', methods=['POST'])
def login():
	username = request.form['username']
	password = request.form['password']
	if username == 'admin' or username == 'user' or username == 'useradmin':
		# Login and validate the user.
		user = load_user(username)
		login_user(user)

		flask.flash('Logged in successfully.')

		identity_changed.send(current_app._get_current_object(),
								  identity=Identity(user.id))

		next = flask.request.args.get('next')
		#if not next_is_valid(next):
		#	return flask.abort(400)

		return flask.redirect(next or flask.url_for('index'))
	return flask.render_template('login.html', form=form)

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
	# Set the identity user object
	identity.user = current_user

	# Add the UserNeed to the identity
	if hasattr(current_user, 'id'):
		identity.provides.add(UserNeed(current_user.id))

	# Assuming the User model has a list of roles, update the
	# identity with the roles that the user provides
	if hasattr(current_user, 'roles'):
		for role in current_user.roles:
			identity.provides.add(RoleNeed(role.name))

@login_manager.user_loader
def load_user(userid):
	if (userid == 'admin'):
		return User(userid, 'Admin', [Role('admin')])
	elif userid == 'user':
		return User(userid, 'Usuario', [Role('user')])
	else: 
		return User(userid, 'Usuario e Admin', [Role('user'), Role('admin')])
	

@login_manager.unauthorized_handler
def unauthorized():
	return "UNAUTHORIZED"

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for('index'))

class User():
	def __init__(self, id, roles):
		print "init user" + id
		self.id = id
		self.authenticated = True
		self.active = True
		self.anonymous = False
		self.roles = roles

	def __init__(self, id, name, roles):
		print "init user" + id
		self.id = id
		self.name = name
		self.authenticated = True
		self.active = True
		self.anonymous = False
		self.roles = roles

	def is_active(self):
		return self.is_active

	def is_authenticated(self):
		return self.is_authenticated

	def is_anonymous(self):
		return self.is_anonymous

	def get_id(self):
		return self.id

class Role():
	def __init__(self, name):
		self.name = name

if __name__ == '__main__':
	print "INIT FLASK"

	use_debugger = True
	app.run(use_debugger=use_debugger, debug=use_debugger)