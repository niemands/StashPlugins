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
	count = 0
	tag = client.findTagIdWithName("CopyTags")
	tag_ids = [tag]

	galleries = client.findGalleriesByTags(tag_ids)

	# TODO: Multithreading
	for gallery in galleries:
		if gallery.get('scene') is not None:
			scene_id = gallery.get('scene').get('id')
			scene = client.getSceneById(scene_id)
			gallery_data = {
				'id': gallery.get('id'),
				'title': scene.get('title')
			}
			if scene.get('details'):
				gallery_data['details'] = scene.get('details')
			if scene.get('url'):
				gallery_data['url'] = scene.get('url')
			if scene.get('date'):
				gallery_data['date'] = scene.get('date')
			if scene.get('rating'):
				gallery_data['rating'] = scene.get('rating')
			if scene.get('studio'):
				gallery_data['studio_id'] = scene.get('studio').get('id')
			if scene.get('tags'):
				tag_ids = [t.get('id') for t in scene.get('tags')]
				gallery_data['tag_ids'] = tag_ids
			if scene.get('performers'):
				performer_ids = [p.get('id') for p in scene.get('performers')]
				gallery_data['performer_ids'] = performer_ids

			client.updateGallery(gallery_data)
			log.LogDebug(f'Copied information to gallery {gallery.get("id")}')
			count += 1

	log.LogInfo(f'Copied scene information to {count} galleries')


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
