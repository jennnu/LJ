import tornado.ioloop
import tornado.web
import jinja2
import os
import httplib2
import sys
import json
import torndb
import bcrypt

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

db = torndb.Connection("localhost:3306", "livejam", "root")

template_dir = os.path.join(os.path.split(os.path.dirname(__file__))[0], 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

DEVELOPER_KEY = "AIzaSyBt4QnophL-y5mXPdjBtHL43AhV0WZqOBE"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

settings = {
	"debug": True,
	"static_path": os.path.join(os.path.dirname(__file__), "static"),
	"cookie_secret": "poBJaxJYT5ydazMnbAaLWlVApjABu0plm8Dr4qjhY+4="
}

server_settings = {
	"xheaders": True
}

class MainHandler(tornado.web.RequestHandler):

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def get_current_user(self):
		return self.get_secure_cookie('email')

class VideoSearchHandler(MainHandler):

	def get(self):
		query = self.get_argument("query", "")
  		videos = self.youtube_search(query)
		self.write(json.dumps(videos))

	def youtube_search(self, query):
		youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
		# Call the search.list method to retrieve results matching the specified
		# query term.
		search_response = youtube.search().list(
	    	q=query,
	    	part="id,snippet",
	    	maxResults=5
	  	).execute()

	  	videos = []
	  	#channels = []
	  	#playlists = []

	  	# Add each result to the appropriate list, and then display the lists of
	  	# matching videos, channels, and playlists.
	  	for search_result in search_response.get("items", []):
	  		#print search_result
	  		if search_result["id"]["kind"] == "youtube#video":
	  			videos.append({
	  				'title': search_result["snippet"]["title"], 
	  				'id': search_result["id"]["videoId"]
	  			})
	  		#elif search_result["id"]["kind"] == "youtube#channel":
	  		#	channels.append("%s (%s)" % (search_result["snippet"]["title"],search_result["id"]["channelId"]))
	  		#elif search_result["id"]["kind"] == "youtube#playlist":
	  		#	playlists.append("%s (%s)" % (search_result["snippet"]["title"], search_result["id"]["playlistId"]))

	  	#print "Videos:\n", "\n".join(videos), "\n"
	  	#print "Channels:\n", "\n".join(channels), "\n"
	  	#print "Playlists:\n", "\n".join(playlists), "\n"
	  	return videos

class MainPage(MainHandler):

	def get(self):
		user = self.current_user
		self.render("index.html", user = user)

class SignupPage(MainHandler):

	def get(self):
		self.render_signup()

	def post(self):
		username = self.get_argument("username")
		email = self.get_argument("email")
		password = self.get_argument("password")
		if username and email and password:
			password = bcrypt.hashpw(password, bcrypt.gensalt())
			userdb = db.execute("""INSERT INTO user (username, email, password, status)
									VALUES (%s, %s, %s, %s)""", username, email, password, 'A')
			self.render_signup('','','',True)
		else:
			error = "Please fill out all fields"	
			self.render_signup(username, email, error)

	def render_signup(self, username = "", email = "", error = "", success = ""):
		self.render("signup.html", username = username, email = email, error = error, success = success)


class LoginPage(MainHandler):

	def get(self):
		self.render("login.html")

	def post(self):
		email = self.get_argument("email")
		password = self.get_argument("password")
		if email and password:
			get_password = db.get(""" SELECT password FROM user WHERE email = %s AND 
										status = 'A' """, email)
		if get_password:
			if bcrypt.hashpw(password, get_password['password']) == get_password['password']:
				self.set_secure_cookie('email', email)
				self.redirect('/')
				return

		error = 'invalid email or password'
		print error

class LogoutHandler(MainHandler):

	def get(self):
		self.clear_cookie('email')
		self.redirect('/')

class AddVideoHandler(MainHandler):

	def post(self):
		vid = self.get_argument("vid")
		user = self.get_current_user()
		get_user = db.get("""SELECT id from user WHERE email = %s AND status = 'A'""", user)
		if user and vid:
			addv = db.execute("""INSERT INTO video (user_id, video_id, status)
								VALUES(%s,%s,%s)""", get_user['id'], vid, 'A')
			self.write("Success!")
		else:
			self.write("error") 

class GetPlaylistHandler(MainHandler):

	def get(self):
		user = self.get_current_user()
		get_user = db.get("""SELECT id from user WHERE email = %s AND status = 'A'""", user)
		video_list = []
		if user:
			q = db.query("""SELECT video_id FROM video WHERE user_id = %s AND status = 'A'""", get_user['id'])
			for v in q:
				video_list.append({
					'vid': v.video_id
					})

		self.write(json.dumps(video_list))



application = tornado.web.Application([
    (r"/", MainPage),
    (r"/videosearch", VideoSearchHandler),
    (r"/signup", SignupPage),
    (r"/login", LoginPage),
    (r"/logout", LogoutHandler),
    (r"/addvideo", AddVideoHandler),
    (r"/getplaylist", GetPlaylistHandler)
], **settings)

if __name__ == "__main__":
    application.listen(8888, **server_settings)
    tornado.ioloop.IOLoop.instance().start()

