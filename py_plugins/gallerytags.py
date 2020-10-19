import json
import sys
import time

import log
from stash_interface import StashInterface

# raw plugins may accept the plugin input from stdin, or they can elect
# to ignore it entirely. In this case it optionally reads from the
# command-line parameters.
def main():
	input = readJSONInput()

	output = {}
	run(input, output)

	out = json.dumps(output)
	print(out + "\n")

def readJSONInput():
	input = sys.stdin.read()
	return json.loads(input)

def run(input, output):
	modeArg = input['args']["mode"]

	try:
		if modeArg == "" or modeArg == "create":
			client = StashInterface(input["server_connection"])
			addTag(client)
		elif modeArg == "remove":
			client = StashInterface(input["server_connection"])
			removeTag(client)
		elif modeArg == "copy":
			client = StashInterface(input["server_connection"])
			copyTags()
	except Exception as e:
		raise
		#output["error"] = str(e)
		#return

	output["output"] = "ok"


def copyTags(client):
	pass


def addTag(client):
	tagName = "CopyTags"
	tagID = client.findTagIdWithName(tagName)

	if tagID == None:
		tagID = client.createTagWithName(tagName)


def removeTag(client):
	tagName = "CopyTags"
	tagID = client.findTagIdWithName(tagName)

	if tagID == None:
		log.LogInfo("Tag does not exist. Nothing to remove")
		return

	log.LogInfo("Destroying tag")
	client.destroyTag(tagID)

main()
