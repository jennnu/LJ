import httplib2
import os
import sys

from handlers import mainhandler

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
#CLIENT_SECRETS_FILE = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)), "config/client_secret.json")

class YoutubeOauthHandler(mainhandler.MainHandler):

	def get(self):
		flow = OAuth2WebServerFlow(client_id='446888909227-htgjn8q42147uv9apsr3dentbe65m0eh.apps.googleusercontent.com',
                           client_secret='EBoh8fkDb7IruVrCAGBddzhg',
                           scope=YOUTUBE_READ_WRITE_SCOPE,
                           redirect_uri='http://localhost:8888/oauth2callback',
                           approval_prompt="force")
		code = self.get_argument("code")
		credentials = flow.step2_exchange(code)
		youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http=credentials.authorize(httplib2.Http()))
		broadcast_id = insert_broadcast(youtube)
		stream_id = insert_stream(youtube)
		bind_broadcast(youtube, broadcast_id, stream_id)
		list_broadcasts(youtube, broadcast_id)
		# post_data = { 'code': code, 
		# 			  'client_id': '446888909227-htgjn8q42147uv9apsr3dentbe65m0eh.apps.googleusercontent.com',
		# 			  'client_secret': 'EBoh8fkDb7IruVrCAGBddzhg',
		# 			  'redirect_uri': 'http://localhost:8888/oauth2callback',
		# 			  'grant_type': 'authorization_code' }

		# body = urllib.urlencode(post_data) #Make it into a post request
		# http_client = tornado.httpclient.AsyncHTTPClient()
		# http_client.fetch("https://accounts.google.com/o/oauth2/token", self.handle_request, method='POST', headers=None, body=body) #Send it off!	  

		

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

# Create a liveBroadcast resource and set its title, scheduled start time,
# scheduled end time, and privacy status.
def insert_broadcast(youtube):

 	insert_broadcast_response = youtube.liveBroadcasts().insert(
 		part="snippet,status",
 		body=dict(
 			snippet=dict(
 				title='Test Title',
 				scheduledStartTime='2015-03-08T00:00:00.000Z',
 				scheduledEndTime='2015-03-09T00:00:00.000Z'
 				),
 			status=dict(
 				privacyStatus="private"
 				)
 			)
 		).execute()

 	snippet = insert_broadcast_response["snippet"]

 	print "Broadcast '%s' with title '%s' was published at '%s'." % (
 		insert_broadcast_response["id"], snippet["title"], snippet["publishedAt"])
 	return insert_broadcast_response["id"]

# Create a liveStream resource and set its title, format, and ingestion type.
# This resource describes the content that you are transmitting to YouTube.
def insert_stream(youtube):
	insert_stream_response = youtube.liveStreams().insert(
		part="snippet,cdn",
		body=dict(
			snippet=dict(
				title='Test Title'
				),
			cdn=dict(
				format="720p",
				ingestionType="rtmp"
				)
			)
		).execute()

	snippet = insert_stream_response["snippet"]

	print "Stream '%s' with title '%s' was inserted." % (
		insert_stream_response["id"], snippet["title"])
	return insert_stream_response["id"]

# # Bind the broadcast to the video stream. By doing so, you link the video that
# # you will transmit to YouTube to the broadcast that the video is for.
def bind_broadcast(youtube, broadcast_id, stream_id):
	bind_broadcast_response = youtube.liveBroadcasts().bind(
		part="id,contentDetails",
		id=broadcast_id,
		streamId=stream_id
		).execute()

	print "Broadcast '%s' was bound to stream '%s'." % (
		bind_broadcast_response["id"],
		bind_broadcast_response["contentDetails"]["boundStreamId"])

# Retrieve a list of broadcasts with the specified status.
def list_broadcasts(youtube, bid):
	print "Broadcasts with id '%s':" % bid

	list_broadcasts_request = youtube.liveBroadcasts().list(
		id=bid,
		part="id,snippet,contentDetails",
		maxResults=50
		)

	if list_broadcasts_request:
		list_broadcasts_response = list_broadcasts_request.execute()

	for broadcast in list_broadcasts_response.get("items", []):
		print "%s (%s) (%s)" % (broadcast["snippet"]["title"], broadcast["id"], broadcast["contentDetails"]["monitorStream"]["embedHtml"])

	list_broadcasts_request = youtube.liveBroadcasts().list_next(
		list_broadcasts_request, list_broadcasts_response)

# Retrieve a list of the liveStream resources associated with the currently
# authenticated user's channel.
def list_streams(youtube):
	print "Live streams:"

	list_streams_request = youtube.liveStreams().list(
		part="id,snippet",
		mine=True,
		maxResults=50
	)
	if list_streams_request:
		list_streams_response = list_streams_request.execute()

	for stream in list_streams_response.get("items", []):
		print "%s (%s)" % (stream["snippet"]["title"], stream["id"])
	
	list_streams_request = youtube.liveStreams().list_next(
		list_streams_request, list_streams_response)

# if __name__ == "__main__":
# 	argparser.add_argument("--broadcast-title", help="Broadcast title",
# 		default="New Broadcast")
# 	argparser.add_argument("--privacy-status", help="Broadcast privacy status",
# 		default="private")
# 	argparser.add_argument("--start-time", help="Scheduled start time",
# 		default='2014-01-30T00:00:00.000Z')
# 	argparser.add_argument("--end-time", help="Scheduled end time",
# 		default='2014-01-31T00:00:00.000Z')
# 	argparser.add_argument("--stream-title", help="Stream title",
# 		default="New Stream")
# 	args = argparser.parse_args()
	
# youtube = get_authenticated_service(args)
# try:
# 	broadcast_id = insert_broadcast(youtube, args)
# 	stream_id = insert_stream(youtube, args)
# 	bind_broadcast(youtube, broadcast_id, stream_id)
# except HttpError, e:
# 	print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)