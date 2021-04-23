import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
import http.client,httplib2

class YT:
	CLIENT_SECRETS_FILE = 'client_secret.json'
	# CREDENTIALS = 'credentials.json'
	PICKLE = 'cred.pickle'
	SCOPES = ['https://www.googleapis.com/auth/youtube','https://www.googleapis.com/auth/youtube.upload']
	API_SERVICE_NAME = 'youtube'
	API_VERSION = 'v3'
	yt = None

	RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
							http.client.IncompleteRead, http.client.ImproperConnectionState,
							http.client.CannotSendRequest, http.client.CannotSendHeader,
							http.client.ResponseNotReady, http.client.BadStatusLine)
	RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
	MAX_RETRIES = 10

	def __init__(self):
		print('Init YT Service')
		import os
		import pickle
		cred = None
		if os.path.exists(self.PICKLE):
			with open(self.PICKLE, 'rb') as token:
				print(f'Using pickle file[{self.PICKLE}]')
				cred = pickle.load(token)
		if not cred or not cred.valid:
			if cred and cred.expired and cred.refresh_token:
				from google.auth.transport.requests import Request
				print('Refreshing cred')
				cred.refresh(Request())
			else:
				print('Opening Web-Browser to get OAuth cred/token')
				flow = InstalledAppFlow.from_client_secrets_file(self.CLIENT_SECRETS_FILE, self.SCOPES)
				cred = flow.run_local_server()
			with open(self.PICKLE, 'wb') as token:
				print(f'Caching cred to pickle [{self.PICKLE}]')
				pickle.dump(cred, token)
		try:
			service = build(self.API_SERVICE_NAME, self.API_VERSION, credentials = cred)
			print(self.API_SERVICE_NAME, 'service created successfully')
			self.yt = service
		except Exception as e:
			print('Unable to connect.')
			print(e)
			self.yt = None
	
	def upload(self,args):
		def _upload(request):
			response = None
			error = None
			retry = 0
			# manual retry, not http retry
			httplib2.RETRIES = 1
			while response is None:
				try:
					print('Uploading file (chunk)...')
					status, response = request.next_chunk()
					print('Status:',status)
					if response is not None:
						if 'id' in response:
							id = {response["id"]}
							print(f'Uploaded Video id "{id}"')
							return id
						else:
							exit(f'Upload failed:{response}')
				except HttpError as e:
					if e.resp.status in self.RETRIABLE_STATUS_CODES:
						error = f'A retriable HTTP error {e.resp.status} occurred:\n{e.content}'
					else:
						raise
				except self.RETRIABLE_EXCEPTIONS as e:
					error = f'A retriable error occurred: {e}'

			if error is not None:
				print(error)
				retry += 1
				if retry > self.MAX_RETRIES:
					exit('No longer attempting to retry.')
				max_sleep = 2 ** retry
				import random, time
				sleep_seconds = random.random() * max_sleep
				print (f'Sleeping {sleep_seconds} seconds and then retrying...')
				time.sleep(sleep_seconds)
	
		print(f'Title:{args["title"]}')
		body = {
			'snippet':{
				'title':args['title'],
				'description':args['description'],
				'tags':args['tags'],
				'categoryId':args['categoryId']
			},
			'snippet':{
				'privacyStatus':args['privacyStatus']
			}
		}

		from googleapiclient.http import MediaFileUpload
		resumable_upload = self.yt.videos().insert(
			part=','.join(body.keys()),
			body=body,
			media_body = MediaFileUpload(args['file'],chunksize=-1,resumable=True)
		)
		id = _upload(resumable_upload)
		return id

	def thumbnail(self,args):
		print(f'Setting thumbnail[{args["file"]}] to videoId [{args["id"]}]')
		self.yt.thumbnails().set(
			videoId=args['id'],
			media_body = args['file']
		).execute()

	def playlistize(self, args):
		# https://github.com/tokland/youtube-upload
		print('Updating playlists')
		def _get_playlist(title):
			request = self.yt.playlists().list(
				mine = True,
				part='id,snippet'
			)
			while request:
				results = request.execute()
				for item in results["items"]:
					t = item.get("snippet", {}).get("title")
					# existing_playlist_title = (t.encode(current_encoding) if hasattr(t, 'decode') else t)
					if t == title:
						print('existing')
						return item.get("id")
				request = self.yt.playlists().list_next(request, results)

		def _create_playlist(title,privacy = 'public'):
			print(f"creating [{title}]")
			response = self.yt.playlists().insert(
				part="snippet,status",
				body={
					"snippet": {"title": title,},
					"status": {"privacyStatus": privacy,}
				}).execute()
			return response.get("id")

		def _add_to_playlist(playlist_id, video_id):
			print(f"Adding [{video_id}] to playlist: [{playlist_id}]")
			return self.yt.playlistItems().insert(
				part="snippet",
				body={
					"snippet": {
						"playlistId": playlist_id,
						"resourceId": {
							"kind": "youtube#video",
							"videoId": video_id,
						}
					}
			}).execute()

		for playlist in args['playlists']:
			print(f'{playlist}:')
			playlist_id = _get_playlist(playlist) or _create_playlist(playlist)
			if playlist_id:
				return self._add_to_playlist(playlist_id, args['id'])
			else:
				print("Error adding video to playlist")

	def get_num(self,args):
		print(f'Getting playlist [{args["title"]}] count')
		request = self.yt.playlists().list(
			mine = True,
			part='id,snippet,contentDetails'
		)
		while request:
			results = request.execute()
			for item in results["items"]:
				t = item.get("snippet", {}).get("title")
				# existing_playlist_title = (t.encode(current_encoding) if hasattr(t, 'decode') else t)
				if t == args['title']:
					return item.get("contentDetails").get("itemCount")
			request = self.yt.playlists().list_next(request, results)

def create_thumbnail(legend, event):
	print(f'Creating thumbnail [{legend}-{event}]')
	from PIL import Image

	def scale(image, size):
		targetWidth = size[0]
		targetHeight = size[1]
		width = image.size[0]
		height = image.size[1]
		if (targetWidth - width) < (targetHeight - height):
			ratio = targetWidth/width
		else:
			ratio = targetHeight/height
		image = image.resize((int(width * ratio), int(height * ratio)))
		return image

	def centrePos(image, size):
		width = image.size[0]
		height = image.size[1]
		targetWidth = size[2] - size[0]
		targetHeight = size[3] - size[1]
		init = [size[0], size[1]]
		if (targetWidth - width) > (targetHeight - height):
			pos = [int((targetWidth-width)//2), 0]
		else:
			pos = [0, int((targetHeight-height)//2)]
		return tuple([sum(x) for x in zip(init, pos)])

	# BG
	canvas = Image.open('pics/bg.png')
	Cwidth = canvas.size[0]
	Cheight = canvas.size[1]

	# Logo
	logo = Image.open('pics/logo.png')
	logo = scale(logo, (Cwidth/2, Cheight))
	canvas.paste(logo, (Cwidth//2, 0), logo)

	# Legend
	legend = Image.open(rf'pics/legends/{legend}.png')
	legend = scale(legend, (Cwidth/2, Cheight))
	pos = centrePos(legend, (0, 0, Cwidth/2, Cheight))
	canvas.paste(legend, pos, legend)

	# Event
	if 'Ranked 1v1' in event:
		ratio = (1,2)
		eventArea = (Cwidth//2, logo.size[1], Cwidth, Cheight)
		innerCanvas = canvas.crop(eventArea)

		eve = 'Silver'
		banner = Image.open(rf'pics/events/{eve}.png')
		bannerWidth = ratio[0] * innerCanvas.size[0]//sum(ratio)
		banner = scale(banner, (bannerWidth, Cheight-logo.size[1]))
		pos = centrePos(banner,(0,0,bannerWidth,innerCanvas.size[1]))
		innerCanvas.paste(banner, pos, banner)

		event = Image.open(rf'pics/events/{event}.png')
		eventWidth = ratio[1] * innerCanvas.size[0]//sum(ratio)
		event = scale(event, (eventWidth, Cheight-logo.size[1]))
		pos = centrePos(event, (bannerWidth,0,eventWidth/2,innerCanvas.size[1]))
		innerCanvas.paste(event, pos, event)

		canvas.paste(innerCanvas, eventArea, innerCanvas)
	else:
		event = Image.open('pics/events/{event}.png')
		event = scale(event, (Cwidth/2, Cheight-logo.size[1]))
		pos = centrePos(event, (Cwidth//2, logo.size[1], Cwidth, Cheight))
		canvas.paste(event, pos, event)

	# Save
	filename = rf'{legend}-{event}.jpg'
	rgb = canvas.convert('RGB')
	rgb.save(filename)
	return filename

yt = YT()
if yt:
	from pathlib import Path
	import os
	path = r'H:\mygits\scripts\beta\yt'
	GAME = 'Brawlhalla'
	DESC = \
'''Brawlhalla is a free platform fighting game with over 40 million players that supports up to 8 online in a single match with full cross-play. Join casual free-for-alls, queue for ranked matches, or make a custom room with your friends. Frequent updates. 50 unique characters and counting. Come fight for glory in the halls of Valhalla!

Features
- Online Ranked 1v1 & 2v2 - Climb the ranked ladder from Tin up to Platinum and beyond! Fight enemies solo or team up with your friends. Matches you against players near your skill level.
- 4 Player Online Free for All - Casual matches where four fighters enter, but only one can win.
- Cross-play Custom Rooms - Invite up to 8 friends on all platforms to a huge variety of custom matches: 4v4s, 1v3, 2v2, FFA, and much more.
- Many Game Modes - Mix things up with Brawlball, Bombsketball, Capture the Flag, Kung-Foot, and many more fun party game modes.
- The Training Room - Practice combos and setups inside the Training Room! Look at detailed frame data, hitboxes, hurtboxes, and sharpen your skills.

Plus: Best-in-class spectating, match recording and replay. Dozens of maps. Single player tournament mode. An online brawl-of-the-week. Experimental mode. Millions of players for fast matchmaking. Regional servers for low-latency online play. Frequent updates. Tons of esports events and tournaments. Excellent support for keyboard and controllers. Career history and cool progress rewards. Ranked seasons. Friendly devs. Fun, fair free-to-play. And much more.

How we do Free to Play:
-Brawlhalla will always be 100% free to play, with no pay-to-win advantages and no in-game purchases keeping you from the action. None of the premium content affects gameplay.
-The Legend Rotation of eight free to play characters changes every week, and you can earn gold to unlock more Legends by playing any online game mode.'''

	files = []
	for file in Path(path).glob('*.mkv'):
		files.append(file)

	for file in files:
		filename = os.path.basename(file)
		# ORION-Ranked 1v1 (Silver)
		try:
			legend, event = [_.strip() for _ in str(filename)[:-4].split('-')]
			print(legend, event)
		except ValueError:
			print(rf'Name format error {file}, skipping')
			continue
		if not os.path.exists(rf'pics/legends/{legend}.png'):
			print(rf'{legend}.png not found, skipping')
			continue
		if not os.path.exists(rf'pics/events/{event}.png'):
			print(rf'{event}.png not found, skipping')
			continue

		# Get # from playlist count
		args={
			'title':event
		}
		num = yt.get_num(args) or 1

		# Title
		# Brawlhalla - ORION - Ranked 1v1 (Silver) - Gameplay (No commentary) Part #40
		title = rf"Temp {GAME} - {legend.upper()} - {event} - Gameplay (No commentary) Part #{num}"

		# Description
		print('Description (r to retry 1, rr or R to start afresh')
		i = 1
		times = []
		while True:
			if i > 3: break
			ip = input(f'(Match:#{i}):')
			if ip == 'rr' or ip == 'R':
				i = 1
				times = []
			elif ip != 'r':
				times.append(f'{ip}')
				i += 1
			print(f'{times}')
		description = "\n".join(times) + '\n' + DESC

		# Upload
		args = {
			'title':title,
			'description':description,
			'tags':['zingamigo','zingamigo gaming'],
			'categoryId':20, #Gaming
			'privacyStatus':'private',
			'file':f'{file}'
		}
		# id = 'WHJl7V8p73M' or yt.upload(args)
		id = yt.upload(args)

		# Thumbnail
		thumbnail_file = create_thumbnail(legend,event)
		args = {
			'id':id,
			'file':thumbnail_file
		}
		yt.thumbnail(args)

		# Setting playlist
		playlists = [
			f'{GAME}',
			f'{GAME} {legend.title()}'
		]
		if event in ['Free For All', 'Friendly 2v2', 'Strikeout 1v1'] or 'Ranked 1v1' in event:
			pass
		else:
			playlists.append(f'{GAME} Brawl of the week')
		args={
			'id':id,
			'playlists':playlists
		}
		yt.playlistize(args)

		print('Update Game Title')
