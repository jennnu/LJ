import tornado.ioloop
import tornado.web
import tornado.httpclient
import jinja2
import os
import httplib2
import sys
import json
import torndb
import bcrypt
import urllib

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

from handlers import broadcast
from handlers import mainhandler

db = torndb.Connection("localhost:3306", "livejam", "root")

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

class VideoSearchHandler(mainhandler.MainHandler):

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

class MainPage(mainhandler.MainHandler):

	def get(self):
		user = self.current_user
		self.render("index.html", user = user)

class SignupPage(mainhandler.MainHandler):

	def get(self):
		self.render_signup()

	def post(self):
		username = self.get_argument("username")
		email = self.get_argument("email")
		password = self.get_argument("password")
		if username and email and password:
			# Todo:
			# check if email already exists in database
			# check if email is correct format
			# check if username already exists
			# maybe check if password is minimum amount of characters
			password = bcrypt.hashpw(password, bcrypt.gensalt())
			userdb = db.execute("""INSERT INTO user (username, email, password, status)
									VALUES (%s, %s, %s, %s)""", username, email, password, 'A')
			self.render_signup('','','',True)
		else:
			error = "Please fill out all fields"	
			self.render_signup(username, email, error)

	def render_signup(self, username = "", email = "", error = "", success = ""):
		self.render("signup.html", username = username, email = email, error = error, success = success)


class LoginPage(mainhandler.MainHandler):

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

class BroadcastPage(mainhandler.MainHandler):

	def get(self):
		self.render("broadcast.html")


class LogoutHandler(mainhandler.MainHandler):

	def get(self):
		self.clear_cookie('email')
		self.redirect('/')

class AddVideoHandler(mainhandler.MainHandler):

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

class GetPlaylistHandler(mainhandler.MainHandler):

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

class YoutubeOauthHandler(mainhandler.MainHandler):

	def get(self):
		code = self.get_argument("code")
		post_data = { 'code': code, 
					  'client_id': '446888909227-htgjn8q42147uv9apsr3dentbe65m0eh.apps.googleusercontent.com',
					  'client_secret': 'EBoh8fkDb7IruVrCAGBddzhg',
					  'redirect_uri': 'http://localhost:8888/oauth2callback',
					  'grant_type': 'authorization_code' }

		body = urllib.urlencode(post_data) #Make it into a post request
		http_client = tornado.httpclient.AsyncHTTPClient()
		http_client.fetch("https://accounts.google.com/o/oauth2/token", self.handle_request, method='POST', headers=None, body=body) #Send it off!	  

		self.redirect("/")

	def handle_request(self, response):
		if response.error:
			print "Error:", response.error
		else:
			json_response = response.body
			token = json.loads(json_response)
			print token['access_token']
			user = self.get_current_user()
			get_user = db.get("""SELECT id from user WHERE email = %s AND status = 'A'""", user)
			update_user = db.execute("""UPDATE user SET youtube_access_token = %s WHERE id = %s""", token['access_token'], get_user['id'])
		return



application = tornado.web.Application([
    (r"/", MainPage),
    (r"/videosearch", VideoSearchHandler),
    (r"/signup", SignupPage),
    (r"/login", LoginPage),
    (r"/logout", LogoutHandler),
    (r"/addvideo", AddVideoHandler),
    (r"/getplaylist", GetPlaylistHandler),
    (r"/oauth2callback", broadcast.YoutubeOauthHandler),
    (r"/broadcast", BroadcastPage)
], **settings)

if __name__ == "__main__":
    application.listen(8888, **server_settings)
    tornado.ioloop.IOLoop.instance().start()

