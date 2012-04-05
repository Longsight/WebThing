from handler import *
from model import User

@handler('login', authed=False)
def get_index():
	pass

@handler(authed=False)
def post_login(username=None, password=None):
	user = User.find(username, password)
	if user == None:
		return 'Login failed'

	session['userId'] = user.id
	redirect(handler.index.get_index)

@handler('register', authed=False)
def get_register():
	pass

@handler(authed=False)
def post_register(username=None, password=None):
	if username == None or password == None:
		return ''

	if len(username) < 3 or len(password) < 8:
		return 'Username must be 3 or more characters.  Password must be 8 or more characters.'

	user = User.add(username, password, False)
	if user == None:
		return 'Username taken.'
	return 'Woot.'

@handler(authed=False)
def get_logout():
	session['userId'] = None

	redirect(handler.index.get_index)
