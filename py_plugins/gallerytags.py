import json
import sys

import log
from stash_interface import StashInterface


def main():
	json_input = read_json_input()

	output = {}
	run(json_input, output)

	out = json.dumps(output)
	print(out + "\n")


def read_json_input():
	json_input = sys.stdin.read()
	return json.loads(json_input)


def run(json_input, output):
	mode_arg = json_input['args']['mode']

	try:
		if mode_arg == "" or mode_arg == "create":
			client = StashInterface(json_input["server_connection"])
			add_tag(client)
		elif mode_arg == "remove":
			client = StashInterface(json_input["server_connection"])
			remove_tag(client)
		elif mode_arg == "copy":
			client = StashInterface(json_input["server_connection"])
			copy_tags(client)
	except Exception:
		raise

	output["output"] = "ok"


def copy_tags(client):
	tag = client.findTagIdWithName("CopyTags")
	tag_ids = [tag]

	galleries = client.findGalleriesByTags(tag_ids)

	for gallery in galleries:
		if gallery.get('scene') is not None:
			# TODO: Get details from scene and add to gallery
			pass


def add_tag(client):
	tag_name = "CopyTags"
	tag_id = client.findTagIdWithName(tag_name)

	if tag_id is None:
		client.createTagWithName(tag_name)


def remove_tag(client):
	tag_name = "CopyTags"
	tag_id = client.findTagIdWithName(tag_name)

	if tag_id is None:
		log.LogInfo("Tag does not exist. Nothing to remove")
		return

	log.LogInfo("Destroying tag")
	client.destroyTag(tag_id)


main()
