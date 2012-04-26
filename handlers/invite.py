import hmac
from datetime import datetime
from time import mktime
from handler import *
from model import *

@handler('invite/index')
def get_index():
	pass

@handler('invite/index')
def post_index(email):
	if u'@' not in email or '\n' in email or '\r' in email or ',' in email:
		return dict(error='Invalid email')
	elif len(User.some(email=email)):
		return dict(alert='Your friend is already a QuestCompanions member')

	code = '%i.%i' % (session.user.id, mktime(datetime.now().timetuple()))
	code += hmac.new(Config.getString('secret_key'), code).hexdigest()

	handler.email(email, 'invite', code=code, username=None if session.user.admin else session.user.username)

	return dict(success=True)

@handler('invite/accept', authed=False)
def get_accept(code=None):
	if session.user != None or code == None:
		redirect(handler.index.get_index)
	return dict(code=code)

@handler('invite/accept', authed=False)
def post_accept(code, username, password, email):
	if session.user != None or code == None:
		redirect(handler.index.get_index)

	error = None
	if User.one(username=username):
		error = u'Username is taken'
	elif len(password) < 6:
		error = u'Password must be at least 6 characters'
	elif u'@' not in email or '\n' in email or '\r' in email or ',' in email:
		error = u'Invalid email'

	if error:
		return dict(code=code, username=username, email=email, error=error)

	user = User.add(username, password, False)
	user.change(email=email)

	session['userId'] = user.id

	redirect(handler.index.get_index)
