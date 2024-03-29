def show_exception_and_exit(exc_type, exc_value, tb):
	import traceback
	traceback.print_exception(exc_type, exc_value, tb)
	input("Press key to exit.")
	sys.exit(-1)

import sys
sys.excepthook = show_exception_and_exit

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
import http.client,httplib2
import sys

def Exit(msg):
	print(msg)
	input('Enter to exit')
	exit()
class YT:
	CLIENT_SECRETS_FILE = './creds/client_secret.json'
	# CREDENTIALS = 'credentials.json'
	PICKLE = './creds/cred.pickle'
	SCOPES = ['https://www.googleapis.com/auth/youtube','https://www.googleapis.com/auth/youtube.upload']
	API_SERVICE_NAME = 'youtube'
	API_VERSION = 'v3'
	yt = None

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
				try:
					cred.refresh(Request())
				except google.auth.exceptions.RefreshError:
					print(f'Got [google.auth.exceptions.RefreshError], so removing {self.PICKLE}')
					os.remove(self.PICKLE)
					input('Rerun session (enter to rereun)')
					os.execl(sys.executable, 'python', __file__, *sys.argv[1:])
					#exit()
			else:
				print('Opening Web-Browser to get OAuth cred/token')
				flow = InstalledAppFlow.from_client_secrets_file(self.CLIENT_SECRETS_FILE, self.SCOPES)
				if len(sys.argv) > 1 and sys.argv[1] == 'link':
					cred = flow.run_console()
				else:
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
		if len(sys.argv) > 1 and sys.argv[1] == 'link':
			Exit('Creds fetched, rerun normally')
	
	def upload(self,args):
		# Not used in this script
		RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
								http.client.IncompleteRead, http.client.ImproperConnectionState,
								http.client.CannotSendRequest, http.client.CannotSendHeader,
								http.client.ResponseNotReady, http.client.BadStatusLine)
		RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
		MAX_RETRIES = 10
	
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
							print(f'Uploaded Video id [{id}]')
							return id
						else:
							Exit(f'Upload failed:{response}')
				except HttpError as e:
					if e.resp.status in RETRIABLE_STATUS_CODES:
						error = f'A retriable HTTP error {e.resp.status} occurred:\n{e.content}'
					else:
						raise
				except RETRIABLE_EXCEPTIONS as e:
					error = f'A retriable error occurred: {e}'

			if error is not None:
				print(error)
				retry += 1
				if retry > MAX_RETRIES:
					Exit('No longer attempting to retry.')
				max_sleep = 2 ** retry
				import random, time
				sleep_seconds = random.random() * max_sleep
				print (f'Sleeping [{sleep_seconds}] seconds and then retrying...')
				time.sleep(sleep_seconds)
	
		print(f'Title:[{args["title"]}]')
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

	def update(self, args):
		print(rf'Updating metadata')
		print(args['title'])
		for line in args['description'].split('\n'):
			if ':' in line:
				print(line)
			else:
				break			
		response = self.yt.videos().list(
			id=args['id'],
			part='snippet,status'
		).execute()

		if not response['items']:
			Exit(f'[{args["id"]}] not found (Is it uploaded?)')
		snippet = response['items'][0]['snippet']
		status = response['items'][0]['status']

		for key,value in args.items():
			snippet[key] = value
		status['selfDeclaredMadeForKids'] =  False
		
		self.yt.videos().update(
			part='snippet,status',
			body=dict(
				snippet = snippet,
				status = status,
				id=args['id']
			)
		).execute()

	def thumbnail(self,args):
		print(f'Setting thumbnail[{args["file"]}] to videoId [{args["id"]}]')
		self.yt.thumbnails().set(
			videoId=args['id'],
			media_body = args['file']
		).execute()

	def add_to_playlists(self, args):
		# https://github.com/tokland/youtube-upload
		print(f'Adding to {len(args["playlists"])} playlists')
		def _is_in_playlist(id,playlistId):
			request = self.yt.playlistItems().list(
				part='snippet',
				playlistId=playlistId,
				maxResults=50
			)

			while request:
				results = request.execute()
				for item in results['items']:
					if item['snippet']['resourceId']['videoId'] == id and '#' in item['snippet']['title']:
						return True
				request = self.yt.playlistItems().list_next(request, results)
			return False

		def _get_playlist(title):
			request = self.yt.playlists().list(
				mine = True,
				part='id,snippet'
			)
			while request:
				results = request.execute()
				for item in results["items"]:
					if item["snippet"]["title"] == title:
						print('existing - ',end='',flush=True)
						return item.get("id")
				request = self.yt.playlists().list_next(request, results)

		def _create_playlist(title,privacy = 'public'):
			print(f"creating - ",end='',flush=True)
			response = self.yt.playlists().insert(
				part="snippet,status",
				body={
					"snippet": {"title": title},
					"status": {"privacyStatus": privacy}
				}).execute()
			return response.get("id")

		def _add_to_playlist(video_id, playlist_id):
			print(f"Adding to playlist")
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
			print(f'Playlist [{playlist}] - ',end='',flush=True)
			playlist_id = _get_playlist(playlist) or _create_playlist(playlist)
			print(f'[{playlist_id}]')
			print(f'\t[{args["id"]}] - ',end='',flush=True)
			if playlist_id:
				if not _is_in_playlist(id,playlist_id):
					_add_to_playlist(args['id'], playlist_id)
				else:
					print(f'Already in playlist')
			else:
				Exit("Error while adding to playlist")

	def get_num(self,args):
		def _get_playlist(title):
			request = self.yt.playlists().list(
				mine = True,
				part='id,snippet'
			)
			while request:
				results = request.execute()
				for item in results["items"]:
					if item["snippet"]["title"] == title:
						return item.get("id")
				request = self.yt.playlists().list_next(request, results)

		botw = args["botw_event"]

		if 'botw' in args["title"]:
			botw = args["botw_event"]
			print(f'# in playlist <{botw}>:',end='',flush=True)
			playlist_id = _get_playlist(f"{GAME} Brawl of the week")
		else:
			print(f'# in playlist [{args["title"]}]:',end='',flush=True)
			playlist_id = _get_playlist(args["title"])

		if playlist_id is None:
			num = 1
			print(f'Fresh playlist: [#{num}]')
			return num
		else:
			del_ids = []
			count = 0
			num = 0
			request = self.yt.playlistItems().list(
				part='contentDetails,snippet',
				playlistId = playlist_id,
				maxResults=50
			)
			while request:
				results = request.execute()
				for item in results["items"]:
					if 'videoPublishedAt' in item['contentDetails']:
						if 'botw' in args["title"]:
							if botw.lower() in item['snippet']['title'].lower():
								count += 1
						else:
							count += 1
					else:
						del_ids.append(item['contentDetails']['videoId'])
					if args['id'] == item['contentDetails']['videoId']:
						num = count
						print(f'Existing [#{num}]')
						break
				request = self.yt.playlistItems().list_next(request, results)
			if not num:
				num = count + 1
				print(f'[#{num}]')
			if del_ids != []:
				print(f'\tDeleted ids in playlist({len(del_ids)}) {[",".join(del_ids)]}')
			return num

	def clean_playlist(self,args):
		Exit('BETA, use at own risk')
		def _get_sorted_playlist(self,args):
			print(f'Retrieving playlist [{args["id"]}] content')
			request = self.yt.playlistItems().list(
				part='snippet,contentDetails',
				playlistId = args['id'],
				maxResults=50
			)
			playlistids = []
			while request:
				results = request.execute()
				for item in results["items"]:
					s = item['snippet']
					playlistids.append([s['resourceId']['videoId'],s['title'],item['contentDetails']['videoPublishedAt']])
				request = self.yt.playlistItems().list_next(request, results)
			from datetime import datetime
			return sorted(playlistids,key = lambda item:datetime.strptime(item[-1], '%Y-%m-%dT%H:%M:%SZ'))

		import re
		# id = 'PLaPl95TYBmHkIC8ObNvWLMiFxf2zXhpyf'
		id = args['id']
		print(f'Cleaning playlist [{id}]')
		args={
			'id':id
		}
		playlist_data = _get_sorted_playlist(args)
		count_dict = {}
		for id,title,filetime in playlist_data:
			print(title)
			curr_title = title
			snippet_title = yt.get_video_details(id)['snippet']['title']
			existing = re.match(r'Brawlhalla (?:#\d+ )?- ([^-#]+) (?:#\d+ )?- ([^-#]+) (?:#\d+ )?- (?:[^#]+) (?:#)?(?:\d+)?',title)
			matched = existing
			legend, event = matched.groups()

			# GAME = 'Brawlhalla'
			if f'{GAME}' in count_dict: count_dict[f'{GAME}'] += 1
			else: count_dict[f'{GAME}'] = 1
			if f'{GAME} {legend}' in count_dict: count_dict[f'{GAME} {legend}'] += 1
			else: count_dict[f'{GAME} {legend}'] = 1
			if f'{GAME} {event}' in count_dict: count_dict[f'{GAME} {event}'] += 1
			else: count_dict[f'{GAME} {event}'] = 1

			# Title
			title = rf"{GAME} #{count_dict[f'{GAME}']} - {legend.upper()} #{count_dict[f'{GAME} {legend}']} - {event} #{count_dict[f'{GAME} {event}']} - Gameplay Part #{count_dict[f'{GAME} {event}']}"
			print(title)
			if curr_title != title:
				args = {
					'id': id,
					'title':title
				}
				yt.update(args)

	def get_video_details(self,id):
		print(f'Getting video details of [{id}]:...',end = '',flush=True)

		request = self.yt.videos().list(
			part='snippet',
			id=id,
		).execute()
		if len(request['items']) == 0:
			Exit(f"[{id}] not found (Deleted?)")
		elif len(request['items']) == 1:
			print(f"[{request['items'][0]['snippet']['title']}]")
			return request['items'][0]
		else:
			print('')
			for item in request['items']:
				print(f"[{item['snippet']['title']}]")
			return request['items']

def create_thumbnail(legend, event):
	print(f'Creating thumbnail [{legend}-{event}]')
	from PIL import Image

	def scale(image, size):
		targetWidth = size[0]
		targetHeight = size[1]
		width = image.size[0]
		height = image.size[1]
		ratio = min(targetWidth/width, targetHeight/height)
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
	print('Painting [bg] on canvas')
	canvas = Image.open(f'{PICS}/bg.png')
	Cwidth = canvas.size[0]
	Cheight = canvas.size[1]

	# Logo
	print(f'Printing [{GAME}] logo')
	logo = Image.open(f'{PICS}/logo.png')
	logo = scale(logo, (Cwidth/2, Cheight))
	canvas.paste(logo, (Cwidth//2, 0), logo)

	# Legend
	print(f'Drawing [{legend}]')
	legend_im = Image.open(rf'{PICS}/legends/{legend}.png')
	legend_im = scale(legend_im, (Cwidth/2, Cheight))
	pos = centrePos(legend_im, (0, 0, Cwidth/2, Cheight))
	canvas.paste(legend_im, pos, legend_im)

	# Event
	print(f'Filling poster of [{event}]')
	if is_ranked:
		event_im = Image.open(rf'{PICS}/events/{event} {tier_event}.png')
	else:
		event_im = Image.open(rf'{PICS}/events/{event}.png')
	event_im = scale(event_im, (Cwidth/2, Cheight-logo.size[1]))
	pos = centrePos(event_im, (Cwidth//2, logo.size[1], Cwidth, Cheight))
	if 'A' in event_im.mode:
		canvas.paste(event_im, pos, event_im)
	else:
		canvas.paste(event_im, pos)

	# Save
	if is_ranked:
		filename = f'{PICS}/cache/{legend}-{event}-{tier_event}.jpg'
	else:
		filename = f'{PICS}/cache/{legend}-{event}.jpg'
	# filename = f'{PICS}/cache/{legend}-{event}.jpg'
	print(f'Saving [{filename}]')
	canvas.convert('RGB').save(filename)
	return filename

yt = YT()
if yt:
	from pathlib import Path
	import os, sys, re
	PICS = r'./files/bhpics'
	GAME = 'Brawlhalla'
	RANKED_EVENT = '1v1 Morph'
	TIERS = ['Silver','Gold']
	SEASON = '22'
	print(f'\nConfig:\n\tRANKED_EVENT={RANKED_EVENT}\n\tSEASON={SEASON}')
	DESC = \
'''
Quicklinks:
-Website: https://www.brawlhalla.com/
-Steam link: https://store.steampowered.com/app/291550/Brawlhalla/
-Recording software: https://obsproject.com/
-Plugin for keyboard overlay: https://github.com/univrsal/input-overlay/releases/

Brawlhalla is a free platform fighting game with over 40 million players that supports up to 8 online in a single match with full cross-play. Join casual free-for-alls, queue for ranked matches, or make a custom room with your friends. Frequent updates. 50 unique characters and counting. Come fight for glory in the halls of Valhalla!

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

	if len(sys.argv) == 2:
		# Whtia212jk|00:00 Win,02:53 Loss,03:56 Win
		id, times = [_.strip() for _ in sys.argv[1].split('|')]
		times = times.split(',')
	elif len(sys.argv) == 1:
		id = input('Video id or link:')
		if 'https' in id:
			linkPrefixes=['https://youtu.be/', 'https://www.youtube.com/watch?v=']
			for prefix in linkPrefixes:
				if prefix in id:
					id = id.replace(prefix,'')
					break
			else:
				Exit(f'Expected [Video id] or links[{linkPrefixes}]')
		times = []
		while True:
			ip = input('times:')
			if ip == '':
				break
			times.append(ip)
	else:
		Exit(f'Incorrect parameters')
	snippet_title = yt.get_video_details(id)['snippet']['title']
	skip_part = r'(?:[^-#]+) (?:#\d+)?'
	brawlhalla_part = s_part = ranked_part = skip_part
	typical_part = r'([^-#]+) (?:#\d+)?'
	legend_part = event_part = typical_part
	# gameplay_part = 'Gameplay \(No commentary\) (?:#\d+ )?'
	gameplay_part = 'Gameplay (?:#\d+ )?'

	existing_event = re.match(rf'{brawlhalla_part} - {legend_part} - {event_part} - {gameplay_part}',snippet_title)
	existing_ranked = re.match(rf'{brawlhalla_part} - {legend_part} - {s_part} - {ranked_part} - {event_part} - {gameplay_part}',snippet_title)
	new = re.match(r'([^-]+)-(.*)',snippet_title)
	matched = existing_ranked or existing_event or new

	is_ranked = False
	is_tier = False

	if existing_event:
		legend, event = matched.groups()
	elif existing_ranked:
		legend, ranked_event = existing_ranked.groups()
		is_ranked = True
		# tier_event = ranked_event
		if ranked_event.split()[1] in TIERS:
			is_tier = True
			tier_event = f'{ranked_event}'
		elif ranked_event.split()[1].lower() == 'morph':
			tier_event = RANKED_EVENT
		else:
			Exit('Improper ranked event')
		event = f'Ranked'
	elif new:
		legend, event = matched.groups()
		event = event.title()
		if 'Ranked' == event.split()[0]:
			is_ranked = True
			ranked_event = event.split()[1]
			if ranked_event in TIERS:
				is_tier = True
				tier_event = f'1v1 {ranked_event}'
			elif ranked_event.lower() == 'morph':
				tier_event = RANKED_EVENT
			else:
				Exit('Improper ranked event')
			event = f'Ranked'
	else:
		Exit("Something crazy!")

	legend = legend.title()
	if is_ranked:
		print(f'[{id}]-[{legend}]-[{event} {tier_event}]')
	else:
		print(f'[{id}]-[{legend}]-[{event}]')

	while not os.path.exists(rf'{PICS}/legends/{legend}.png'):
		input(rf'Legend:{legend}.png not found. Add and enter to continue')
	if is_ranked:
		while not os.path.exists(rf'{PICS}/events/{event} {tier_event}.png'):
			input(rf'Event:[{event} {tier_event}.png] not found. Add and enter to continue')
	else:
		while not os.path.exists(rf'{PICS}/events/{event}.png'):
			input(rf'Event:[{event}.png] not found. Add and enter to continue')
	print('')

	# Get # from playlist count
	nums = {}
	playlists = [f'',f' {legend}',f' {event}']
	botw_event = ''
	if is_ranked:
		playlists.append(f' S{SEASON} Ranked')
		if is_tier:
			playlists.append(f' Ranked {tier_event}')
		else:
			playlists.append(f' S{SEASON} Ranked {RANKED_EVENT}')
	elif event not in ['Free For All', 'Friendly 2v2', 'Strikeout 1v1', 'Experimental 1v1']:
		botw_event = event
		playlists[-1] = f' Brawl of the week'
		playlists.append(f' botw_event')

	for i, playlist in enumerate(playlists):
		playlists[i] = f'{GAME}{playlist}'
	print(playlists)
	for i,playlistname in enumerate(playlists):
		# print(id,playlistname)
		args={
			'title':playlistname,
			'botw_event':botw_event,
			'pos':i, #Not generic
			'id':id
		}
		nums[playlistname] = yt.get_num(args)
	print('')
	# Title
	# Brawlhalla #49 - ORION #5 - Ranked 1v1 (Silver) #4 - Gameplay Part #40
	if event in ['Free For All', 'Friendly 2v2', 'Strikeout 1v1', 'Experimental 1v1']:
		title = rf"{GAME} #{nums[f'{GAME}']} - {legend.upper()} #{nums[f'{GAME} {legend}']} - {event} #{nums[f'{GAME} {event}']} - Gameplay Part #{nums[f'{GAME} {event}']}"
	elif is_ranked:
		brawlhalla_num = f"{GAME} #{nums[f'{GAME}']} "
		legend_num = f" {legend.upper()} #{nums[f'{GAME} {legend}']} "
		s_num = f" S{SEASON} #{nums[f'{GAME} S{SEASON} {event}']} "
		ranked_num = f" Ranked #{nums[f'{GAME} Ranked']} "
		if is_tier:
			event_num = f" {tier_event} #{nums[f'{GAME} Ranked {tier_event}']} "
		else:
			event_num = f" {tier_event} #{nums[f'{GAME} S{SEASON} Ranked {tier_event}']} "
		gameplay_num = f" Gameplay Part #{nums[f'{GAME} {event}']}"

		title = rf"{brawlhalla_num}-{legend_num}-{s_num}-{ranked_num}-{event_num}-{gameplay_num}"
	else:
		title = rf"{GAME} #{nums[f'{GAME}']} - {legend.upper()} #{nums[f'{GAME} {legend}']} - {event} #{nums[f'{GAME} botw_event']} - Gameplay Part #{nums[f'{GAME} Brawl of the week']}"
	# Description
	description = "\n".join(times) + '\n\n' + DESC

	# Update
	tags = ['zingamigo','zingamigo gaming','amigo','amigocnc','zing']
	if f'S{SEASON}' in title:
		tags.extend([f'S{SEASON}',f'Ranked',f'Season {SEASON}'])
	args = {
		'id': id,
		'title':title,
		'description':description,
		'tags':tags,
		'categoryId':20, #Gaming
		'privacyStatus':'public'
	}
	yt.update(args)
	print('')

	# Thumbnail
	thumbnail_file = create_thumbnail(legend,event)
	args = {
		'id':id,
		'file':thumbnail_file
	}
	yt.thumbnail(args)
	print('')

	if botw_event != '':
		del(playlists[-1])
	args={
		'id':id,
		'playlists':playlists
	}
	yt.add_to_playlists(args)

input('Done, Enter to exit')