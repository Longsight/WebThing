import os
import sqlalchemy as sa
from sqlalchemy.types import *

from metamodel import *
import hashlib

@Model
class Character(object):
	id = PrimaryKey(Integer)
	user_id = ForeignKey(Integer, 'User.id')
	game_id = ForeignKey(Integer, 'Game.id')

	name = Unicode()
	server = Nullable(Unicode())
	attrs = String()

@Model
class Game(object):
	name = Unicode()
	characters = Character.relation(backref='game')

@Model
class User(object):
	enabled = Boolean
	admin = Boolean
	username = Unicode(255)
	password = String(40)

	characters = Character.relation(backref='user')

	@staticmethod
	def hash(password):
		salt = ''.join('%02x' % ord(c) for c in os.urandom(24))
		for i in range(1000):
			password = hashlib.sha1(salt + password + salt).hexdigest()
		return salt+password

	@staticmethod
	def checkHash(hash, password):
		salt, hash = hash[:48], hash[48:]
		for i in range(1000):
			password = hashlib.sha1(salt + password + salt).hexdigest()
		if password == hash:
			return True
		return False

	@staticmethod
	def add(username, password, admin):
		if User.one(enabled=True, username=username):
			return None
		with session:
			user = User.create(
				enabled=True, 
				username=username, 
				password=User.hash(password), 
				admin=admin
			)
		return user
	
	@staticmethod
	def find(username, password):
		if username == None or password == None:
			return None
		user = User.one(enabled=True, username=username)
		if user and User.checkHash(user.password, password):
			return user
		return None
	
	def change(self, username, password, admin):
		if password == None:
			password = self.password
		else:
			password = User.hash(password)
		with session:
			self.update(username=username, admin=admin, password=password)

@Model
class Config(object):
	name = String(20)
	value = Unicode(255)

	@staticmethod
	def get(name):
		try:
			return Config.one(name=name).value
		except:
			return None

	@staticmethod
	def getString(name):
		data = Config.get(name)
		if data == None:
			return None
		else:
			return str(data)

	@staticmethod
	def set(name, value):
		with session:
			try:
				row = Config.one(name=name)
				row.update(value=unicode(value))
			except:
				Config.create(
					name=name,
					value=unicode(value)
				)

@setup
def init():
	with session:
		Game.create(name=u'World of Warcraft')
		Game.create(name=u'Star Wars: The Old Republic')

	User.add(u'admin', 'admin', True)