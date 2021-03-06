#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
import vk_api
import requests
import time
import threading
import os

from mildlylib import *

#   Settings   ##############################################
groups = [
	{
		"subreddit": "mildlyinteresting",
		"group_id": -180517625
	}
]

max_posts = 24
max_retries = max_posts * 2
time_between = 3600
#############################################################

#   Persistent vars   #######################################
retries = 0
info = {
	"version": "21.08.19",
	"author": "vk.com/btvoidx"
}
headers = {
	"User-Agent": "Python Automatic posts grabber (by /u/btvoidx)"
}
#############################################################

# Uploading photo to VK is very annoying process. Why i just cant add images to post using urls?
def uploadPhoto(vk, url, group_id, album_id):
	destination = vk.photos.getUploadServer(album_id = album_id, group_id = abs(group_id))

	image = requests.get(url, stream = True)
	data = ("image.jpg", image.raw, image.headers['Content-Type'])
	meta = requests.post(destination['upload_url'], files = {'photo': data}).json()
	return vk.photos.save(group_id = group_id, album_id = album_id, **meta)[0]

def uploadVideo(vk, url, group_id, title):
	video = requests.get(url, stream = True)
	destination = vk.video.save(name = title, group_id = abs(group_id), no_comments = True, repeat = True)

	data = ("video.mp4", video.raw, video.headers['Content-Type'])
	requests.post(destination['upload_url'], files = {'video_file': data}).json()
	return destination

# Make sure script can download image/video with url.
def validateURL(url, media, is_video):
	if is_video == True:
		url = media["reddit_video"]["fallback_url"]
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
			retries += 1
			current_retries += 1
			if retries > max_retries or current_retries >= 10:
				log("Hit barrier of maximum fails. Terminating.", "FATAL")
				return None
			log(failtext, "WARN")
			time.sleep(3)

# Main function.
def main(user_token, subreddit, group_id, post_time):
	log(f"Started parsing {subreddit} for {group_id}.", "TRACE")

	vk_session = vk_api.VkApi(
		token = user_token
	)
	vk = vk_session.get_api()

	r = failproof(
		"Reddit data grab failed.",
		requests.get,
		url = f"https://www.reddit.com/r/{subreddit}/top.json?sort=hot&limit={max_posts}&raw_json=1", headers = headers
	)

	album = vk.photos.getAlbums(owner_id = group_id, count = 1)["items"][0]
	if album["size"] > 9950:
		n = int(album["title"].split(" ")[-1]) + 1
		album = vk.photos.createAlbum(title = f"Chapter {n}", group_id = abs(group_id), comments_disabled = True, upload_by_admins_only = True)

	album_id = album["id"]

	for counter, post in enumerate(r.json()["data"]["children"], start = 1):
		# I don't use here failproof() because script CAN work without printing result. It's not a big problem if it can't print it.
		try:
			log("Post {} of {}; title: {}; media url: {}; subreddit: {}".format(
					counter, max_posts,
					post["data"]["title"].encode("utf-8"),
					post["data"]["url"].encode("utf-8"),
					post["data"]["subreddit"].encode("utf-8"),
				),
				"INFO"
			)
		except:
			log(f"Can't print result of post {counter}. Trying to continue.", "WARN")

		message = f"{post['data']['title']}\n\n/u/{post['data']['author']}"
		post_time += time_between


		newurl = failproof(
			f"URL validation failed. {post['data']['url']}",
			validateURL,
			url = post["data"]["url"], media = post["data"]["media"], is_video = post["data"]["is_video"]
		)

		if post["data"]["is_video"] == True:
			video = failproof(
				f"Failed to upload video to VK. {newurl}",
				uploadVideo,
				vk = vk, url = ewurl, group_id = abs(group_id), title = post["data"]["title"]
			)
			media = "video" + str(group_id) + "_" + str(video["video_id"])
		else:
			image = failproof(
				f"Failed to upload photo to VK. {newurl}",
				uploadPhoto,
				vk = vk, url = newurl, group_id = abs(group_id), album_id = album_id
			)
			media = "photo" + str(group_id) + "_" + str(image["id"])


		failproof(
			f"Unable to schedule post. {message}",
			vk.wall.post,
			owner_id = group_id, message = message, publish_date = post_time, attachments = media, copyright = f"https://www.reddit.com{post['data']['permalink']}"
		)

if __name__ == '__main__':
	token = os.environ["user-token"]
	post_time = int(time.time()) + 1800
	for everything in groups:
		threading.Thread(target=main, args=[token, everything["subreddit"], everything["group_id"], post_time]).start()
