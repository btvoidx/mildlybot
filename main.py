#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
import vk_api
import requests
import time
import threading
import os
import pymongo

from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from random import randint

from mildlylib import *

events = []

def random_id(): #Random number for random_id
	return randint(0, 9223372036854775807)

def failsafe(function, contin=False, *args):
	while contin:
		try:
			return function(*args)
		except Exception as e:
			log(f"An error occurred while executing {function}: {e}", "ERROR")

def eventloop(vk_session):
	while True:
		try:
			longpoll = VkBotLongPoll(vk_session, "180517625")
			log("Connected to longpoll", "TRACE")
		except:
			continue

		try:
			for event in longpoll.listen():
				events.append(event)
		except Exception as e:
			log(f"An error occurred: {e}.", "ERROR")

def main(token):
	vk_session = vk_api.VkApi(
		token=token
	)
	vk = vk_session.get_api()
	threading.Thread(target=eventloop, args=[vk_session]).start()
	torem = []

	while True:
		try:
			for e in torem:
				events.remove(e)
			torem = []
			for event in events: # Parsing through every event
				torem.append(event)
				if event.type == VkBotEventType.WALL_POST_NEW:
					is_auto = False
					is_ad = False

					if event.obj.text.split("\n")[-1][0:3] == "/u/": # If this is an automatic publication
						is_auto = True

					if event.obj.marked_as_ads == 1: # If post is marked as ad
						is_ad = True



					if not is_ad: # If ad-free
						for entry in col.find({"mailing_level": 3},{}):
							message = localization.new_post + "\n\n" + localization.mailing_notification
							vk.messages.send(peer_id=entry["_id"], random_id=random_id(), message=message, attachment=f"wall{event.obj.owner_id}_{event.obj.id}")

					elif not is_ad and not is_auto: # If ad-free and not automatic
						for entry in col.find({"mailing_level": 2},{}):
							message = localization.new_post + "\n\n" + localization.mailing_notification
							vk.messages.send(peer_id=entry["_id"], random_id=random_id(), message=message, attachment=f"wall{event.obj.owner_id}_{event.obj.id}")

				if event.type == VkBotEventType.MESSAGE_NEW:
					if event.obj.text != "":
						log(f"New message: {event.obj.text}", "MSG")
						text = event.obj.text.lower()
						words = text.split()

						if words[0][0] in ["/", "!", "."]: # Removing forced command prefix 
							command = words[0][1:]
						else:
							command = words[0]

						try:
							subcommand = words[1]
						except:
							subcommand = ""

						try:
							ssubcommand = words[2]
						except:
							ssubcommand = ""

						DB = col.find_one({"_id": event.obj.peer_id},{"_id": 0})
						if DB == None: # If peer_id not in DB, create it
							DB = {"_id": event.obj.peer_id, "mailing_level": 0}
							col.insert_one(DB)
							log("New document was created", "DB")

						if command in ["рассылка"]: # Commands
							if command == "рассылка":
								if subcommand == "":
									message = f"{localization.mailing_level_current}\n"
									if DB["mailing_level"] == 0:
										message = message + f"{localization.mailing_level_0}"
									elif DB["mailing_level"] == 1:
										message = message + f"{localization.mailing_level_1}"
									elif DB["mailing_level"] == 2:
										message = message + f"{localization.mailing_level_2}"
									elif DB["mailing_level"] == 3:
										message = message + f"{localization.mailing_level_3}"
									message = message + f"\n{localization.mailing_level_howtochange}"

								elif subcommand in ["0", "1", "2", "3"]:
									message = f"{localization.mailing_level_changed}\n{localization.now} "
									if subcommand == 0:
										message = message + f"{localization.mailing_level_0}"
									elif subcommand == 1:
										message = message + f"{localization.mailing_level_1}"
									elif subcommand == 2:
										message = message + f"{localization.mailing_level_2}"
									elif subcommand == 3:
										message = message + f"{localization.mailing_level_3}"
									col.update_one({"_id": event.obj.peer_id}, {"$set":{"mailing_level":int(subcommand)}})

								else:
									message = f"{localization.mailing_level_invalid}\n0 - {localization.mailing_level_0}\n1 - {localization.mailing_level_1}\n2 - {localization.mailing_level_2}\n 3 - {localization.mailing_level_3}"

								vk.messages.send(peer_id=event.obj.peer_id, random_id=random_id(), message=message)

						else:
							if not event.from_chat:
								message = f"{localization.invalid_command}"
								vk.messages.send(peer_id=event.obj.peer_id, random_id=random_id(), message=message)

		except Exception as e:
			log(f"Shit happened: {e}", "ERROR")

if __name__ == '__main__':
	col = pymongo.MongoClient(os.environ["MONGODB_URI"], retryWrites=False)[os.environ["MONGODB_URI"].split("/")[-1]]["users"]

	token = os.environ["group-token"]
	threading.Thread(target=main, args=[token]).start()