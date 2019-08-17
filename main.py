#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
import vk_api
import requests
import time

#   Settings   ##############################################
groups = [
	{
		"subreddit":"mildlyinteresting", 
		"group_id":-180517625, 
		"album_id":261824317
	}
]

max_posts = 24
max_retries = max_posts * 2
time_between = 3600
#############################################################

#   Persistent vars   #######################################
retries = 0
info = {
	"version": "19.07.15",
	"author": "vk.com/btvoidx"
}
headers = {
	"User-Agent": "Python Automatic posts grabber (by /u/btvoidx)"
}
#############################################################

# Uploading photo to VK is very annoying process. Why i just cant add images to post using urls?
def uploadPhoto(vk, url, group_id, album_id):
	destination = vk.photos.getUploadServer(album_id=album_id, group_id=abs(group_id))

	image = requests.get(url, stream=True)
	data = ("image.jpg", image.raw, image.headers['Content-Type'])
	meta = requests.post(destination['upload_url'], files={'photo': data}).json()
	photo = vk.photos.save(group_id=group_id, album_id=album_id, **meta)[0]
	return photo

def uploadVideo(vk, url, group_id, title):
	video = requests.get(url, stream=True)
	destination = vk.video.save(name=title, group_id=abs(group_id), no_comments=True, repeat=True)

	data = ("video.mp4", video.raw, video.headers['Content-Type'])
	requests.post(destination['upload_url'], files={'video_file': data}).json()
	return video

# Make sure script can download image/video with url.
def validateURL(url, media, is_video):
	if is_video == True:
		url = media["reddit_video"]["fallback_url"]
		return url
	else:
		url = url.replace("://imgur.com", "://i.imgur.com")
		if url.split(".")[-1] not in ["png", "jpg", "jpeg", "gif"]:
			url = url + ".png"
		return url

# Repeat given function when fails
def failproof(failtext, function, **kwargs):
	global retries
	current_retries = 0
	while True:
		try:
			return function(**kwargs)
		except:
			retries = retries + 1
			current_retries = current_retries + 1
			if retries > max_retries or current_retries >= 5:
				return False
			print(failtext)
			time.sleep(3)

def loadtokens(file):
	token = open(file).read()
	return token

# Main function.
def main(user_token, subreddit, group_id, album_id, post_time):
	print("\n{}\nGroup: {}; Subreddit: {}.\n".format(time.strftime("[%Y-%m-%e %H:%M:%S]"), group_id, subreddit))

	vk_session = vk_api.VkApi(
		token=user_token
	)
	vk = vk_session.get_api()

	r = failproof(
		"Reddit data grab failed.",
		requests.get,
		url="https://www.reddit.com/r/{}/top.json?sort=hot&limit={}&raw_json=1".format(subreddit, max_posts), headers=headers
	)

	counter = 0
	for post in r.json()["data"]["children"]:
		counter = counter + 1
		# I don't use here failproof() because script CAN work without printing result. It's not a big problem if it can't.
		try:
			print("Post {} of {}:\nSubreddit: {};\nTitle: {};\nFrom: {};\nImage URL: {}.\n".format(
				counter, max_posts,
				post["data"]["subreddit"].encode("utf-8"),
				post["data"]["title"].encode("utf-8"),
				post["data"]["author"].encode("utf-8"),
				post["data"]["url"].encode("utf-8")
			)
		)
		except:
			print("Can't print result of post {}. Trying to continue.".format(counter))

		message = "{}\n\n/u/{}".format(post["data"]["title"], post["data"]["author"])
		post_time = post_time + time_between

		
		newurl = failproof(
			"URL validation failed.",
			validateURL,
			url=post["data"]["url"], media=post["data"]["media"], is_video=post["data"]["is_video"]
		)

		if post["data"]["is_video"] == True:
			video = failproof(
				"Failed to upload video to VK.",
				uploadVideo,
				vk=vk, url=newurl, group_id=abs(group_id), title=post["data"]["title"]
			)
			media = "video" + str(group_id) + "_" + str(video["video_id"])
		else:
			image = failproof(
				"Failed to upload photo to VK.",
				uploadPhoto,
				vk=vk, url=newurl, group_id=abs(group_id), album_id=album_id
			)
			media = "photo" + str(group_id) + "_" + str(image["id"])

	
		failproof(
			"Unable to schedule post. {}".format(message),
			vk.wall.post,
			owner_id=group_id, message=message, publish_date=post_time, attachments=media
		)
		
if __name__ == '__main__':
	token = loadtokens("tokens.ignore")
	post_time = int(time.time()) + 120 # Adding 120 seconds because i running this script 2 minutes before *:00. My host is very busy doing all tasks at *:00
	for everything in groups:
		main(token, everything["subreddit"], everything["group_id"], everything["album_id"], post_time)