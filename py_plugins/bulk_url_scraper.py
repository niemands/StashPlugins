import json
import sys
from urllib.parse import urlparse
import time

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
		if mode_arg == "" or mode_arg == "scrape":
			client = StashInterface(json_input["server_connection"])
			bulk_scrape(client)
		# TODO: Tag creation
	except Exception:
		raise

	output["output"] = "ok"


def __bulk_scrape(client, scenes, create_missing_performers=False, create_missing_tags=False, create_missing_studios=False, delay=5):
	missing_scrapers = list()

	count = 0

	# Scrape if url not in missing_scrapers
	for scene in scenes:
		if urlparse(scene.get("url")).netloc not in missing_scrapers:
			# TODO: Use delay between scrapes
			scraped_data = client.scrapeSceneURL(scene.get('url'))
			# If result is null, add url to missing_scrapers
			if scraped_data is None:
				log.LogWarning(f"Missing scraper for {urlparse(scene.get('url')).netloc}")
				missing_scrapers.append(urlparse(scene.get('url')).netloc)
				continue
			# No data has been found for this scene
			if not any(scraped_data.values()):
				log.LogInfo(f"Could not get data for scene {scene.get('id')}")
				continue

			# Create dict with scene data
			update_data = {
				'id': scene.get('id')
			}
			if scraped_data.get('title'):
				update_data['title'] = scraped_data.get('title')
			if scraped_data.get('details'):
				update_data['details'] = scraped_data.get('details')
			if scraped_data.get('date'):
				update_data['date'] = scraped_data.get('date')
			if scraped_data.get('image'):
				update_data['cover_image'] = scraped_data.get('image')
			if scraped_data.get('tags'):
				tag_ids = list()
				for tag in scraped_data.get('tags'):
					if tag.get('stored_id'):
						tag_ids.append(tag.get('stored_id'))
					else:
						if create_missing_tags and tag.get('name') != "":
							# Capitalize each word
							tag_name = " ".join(x.capitalize() for x in tag.get('name').split(" "))
							log.LogDebug(f'Create missing tag: "{tag_name}"')
							tag_id = client.createTagWithName(tag_name)
							tag_ids.append(tag_id)
				if len(tag_ids) > 0:
					update_data['tag_ids'] = tag_ids

			if scraped_data.get('performers'):
				performer_ids = list()
				for performer in scraped_data.get('performers'):
					if performer.get('stored_id'):
						performer_ids.append(performer.get('stored_id'))
					else:
						if create_missing_performers and performer.get('name') != "":
							performer_name = " ".join(x.capitalize() for x in performer.get('name').split(" "))
							log.LogDebug(f'Create missing performer: "{performer_name}"')
							performer_id = client.createPerformerByName(performer_name)
							performer_ids.append(performer_id)
				if len(performer_ids) > 0:
					update_data['performer_ids'] = performer_ids

			if scraped_data.get('studio'):
				studio = scraped_data.get('studio')
				if studio.get('stored_id'):
					update_data['studio_id'] = studio.get('stored_id')
				else:
					if create_missing_studios:
						studio_name = " ".join(x.capitalize() for x in studio.get('name').split(" "))
						log.LogDebug(f'Creating missing studio "{studio_name}"')
						studio_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(scene.get('url')))
						studio_id = client.createStudio(studio_name, studio_url)
						update_data['studio_id'] = studio_id

			# Update scene with scraped scene data
			client.updateScene(update_data)
			log.LogDebug(f"Scraped data for scene {scene.get('id')}")
			count += 1

	return count


def bulk_scrape(client, create_missing_performers=False, create_missing_tags=False, create_missing_studios=False, delay=5):
	# Search for all scenes with scrape tag
	tag = client.findTagIdWithName("scrape")
	if tag is None:
		sys.exit("Tag scrape does not exist. Please create it via the 'Create scrape tag' task")

	tag_ids = [tag]
	scenes = client.findScenesByTags(tag_ids)
	log.LogInfo(f'Found {len(scenes)} scenes with scrape tag')
	count = __bulk_scrape(client, scenes, create_missing_performers, create_missing_tags, create_missing_studios, delay)
	log.LogInfo(f'Scraped data for {count} scenes')


main()
