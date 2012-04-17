import math, json, os
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.types import *

from metamodel import *
import hashlib
import markdown2

@Model
class FAQ(object):
	creator_id = ForeignKey(Integer, 'User.id')
	question = Unicode()
	answer = Unicode()
	answer_markdown = Unicode()

@Model
class News(object):
	creator_id = ForeignKey(Integer, 'User.id')
	headline = Unicode()
	story = Unicode()
	story_markdown = Unicode()

	@staticmethod
	def getLast(number=5):
		return transact.query(News).order_by(News.id.desc()).limit(number).all()

# Games
WOW = 1
SWTOR = 2

def gamename(id):
	if id == WOW:
		return 'WoW'
	elif id == SWTOR:
		return 'SW:TOR'

@Model
class GoldHistory(object):
	user_id = ForeignKey(Integer, 'User.id')
	date = DateTime
	amount = Integer
	balance = Integer
	dollars = Integer
	job_id = ForeignKey(Integer, 'Job.id', nullable=True)
	desc = Unicode

@Model
class Bid(object):
	job_id = ForeignKey(Integer, 'Job.id')
	char_id = ForeignKey(Integer, 'Character.id')
	amount = Integer
	date = DateTime
	accepted = Boolean

	def accept(self):
		with transact:
			self.update(accepted=True)
			self.job.update(accepted_date=datetime.now())

@Model
class Job(object):
	user_id = ForeignKey(Integer, 'User.id')
	char_id = ForeignKey(Integer, 'Character.id')
	game = Integer
	created_date = DateTime

	max_pay = Integer
	time_reqd = Integer
	desc = Unicode(140)
	reqs = String

	bids = Bid.relation(backref='job')

	accepted_date = Nullable(DateTime())
	timer_flags = Integer
	timer_started = Nullable(DateTime())
	completed = Boolean
	fee_paid = Integer

	gold_history = GoldHistory.relation(backref='job')

	@staticmethod
	def add(char, max_pay, time_reqd, desc, **kwargs):
		with transact:
			return Job.create(
				user=char.user, 
				char=char, 
				game=char.game, 
				created_data=datetime.now(), 
				max_pay=max_pay, 
				time_reqd=time_reqd,
				desc=desc, 
				reqs=json.dumps(kwargs), 
				timer_flags=0, 
				completed=False, 
				fee_paid=0
			)

	def gamename(self):
		return gamename(self.game)

	def bid(self, char, amount):
		with transact:
			return Bid.create(
					job=self, 
					char=char, 
					amount=amount, 
					date=datetime.now()
				)

	def complete(self):
		accepted = None
		for bid in self.bids:
			if bid.accepted:
				accepted = bid
				break
		assert accepted
		accepted_user = accepted.char.user
		with transact:
			fee = int(math.ceil(float(accepted.amount) * 0.3))
			earned = accepted.amount-fee
			self.update(completed=True, fee_paid=fee)
			self.user.update(gold=self.user.gold-accepted.amount)
			GoldHistory.create(
					user=self.user, 
					date=datetime.now(), 
					amount=-accepted.amount, 
					balance=self.user.gold, 
					job=self, 
					desc=u'Paid %i gold for a job' % accepted.amount
				)
			accepted_user.update(gold=accepted_user.gold+earned)
			GoldHistory.create(
					user=accepted_user, 
					date=datetime.now(), 
					amount=earned, 
					balance=accepted_user.gold, 
					job=self,
					desc=u'Earned %i gold for a job' % (earned)
				)

@Model
class Character(object):
	user_id = ForeignKey(Integer, 'User.id')
	game = Integer

	name = Unicode()
	server = Nullable(Unicode())
	avatar = String()
	attrs = String()
	last_update = Date()

	jobs = Job.relation(backref='char')
	bids = Bid.relation(backref='char')

	def gamename(self):
		return gamename(self.game)

	def link(self, cls='charLink'):
		from handler import handler
		return '<a class="%s" data-char=%s href="%s">%s</a>' %\
			(cls, self.json(), handler.char.get_index.url(self.id), self.name.replace('<', '&lt;'))

	def imagelink(self, cls='charLink'):
		from handler import handler
		return '<a class="%s" data-char=%s href="%s"><img src="%s" alt="%s"></a>' %\
			(cls, self.json(), handler.char.get_index.url(self.id), 
			 self.avatar.replace('"', '&quot;'), self.name.replace('"', '&quot;'))

	def json(self):
		val = json.dumps(dict(
				game=gamename(self.game), 
				name=self.name, 
				server=self.server, 
				avatar=self.avatar
			))
		val = '"%s"' % val.replace('"', '&quot;')
		return val

@Model
class User(object):
	enabled = Boolean
	admin = Boolean
	username = Unicode(255)
	password = String(40)
	gold = Integer
	phone_number = String
	phone_verified = Boolean
	verification_code = Integer
	verification_tries = Integer

	characters = Character.relation(backref='user')
	news = News.relation(backref='creator')
	jobs = Job.relation(backref='user')
	gold_history = GoldHistory.relation(backref='user')

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
		with transact:
			return User.create(
				enabled=True, 
				username=username, 
				password=User.hash(password), 
				admin=admin, 
				gold=0, 
				phone_number='', 
				phone_verified=False, 
			)
	
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
		with transact:
			self.update(username=username, admin=admin, password=password)

	def addGold(self, amount, price):
		with transact:
			self.update(gold=self.gold+amount)
			GoldHistory.create(
					user=self, 
					date=datetime.now(), 
					amount=amount, 
					balance=self.gold, 
					dollars=price, 
					job=None, 
					desc=u'Bought %i gold for $%i' % (amount, price)
				)

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
		with transact:
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
	admin = User.add(u'admin', 'admin', True)
	print User.add(u'foo', 'password', False)
	print User.add(u'bar', 'password', False)

	with transact:
		News.create(
				creator=admin, 
				headline=u'This is a news story', 
				story=u'With a body',
				story_markdown=markdown2.markdown(u'With a body')
			)
		News.create(
				creator=admin, 
				headline=u'This is another news story', 
				story=u'With another body',
				story_markdown=markdown2.markdown(u'with a body')
			)
		FAQ.create(
				creator=admin, 
				question=u'Do you have anything without spam in it?', 
				answer=u'Why would you want that?!',
				answer_markdown=markdown2.markdown(u'Why would you want that?!')
			)
