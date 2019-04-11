#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
import requests
from os import system, chdir, getcwd

repo = "btvoidx/mildlybot"
filename = "main.py"
chdir(getcwd() + "/autoreddit/")

with open(filename) as f:
	current = f.read()
	downloaded = requests.get("https://raw.githubusercontent.com/{}/master/{}".format(repo, filename)).text

	if current == downloaded:
		print("Script is up to date!")
	else:
		print("Script update detected! Updating!")
		f.close()
		f = open(filename, "w")
		f.write(downloaded)

	f.close()
	system("python3.7 {}".format(filename))