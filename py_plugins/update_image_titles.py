import json
import sys
import log
from stash_interface import StashInterface


def main():
    json_input = readJSONInput()

    client = StashInterface(json_input.get('server_connection'))
    update_image_titles(client)

    output = {
        'output': 'ok'
    }

    print(json.dumps(output) + '\n')


def readJSONInput():
    json_input = sys.stdin.read()
    return json.loads(json_input)


def update_image_titles(client):
    log.LogInfo('Getting all images...')
    images = client.findImages()
    total = len(images)
    log.LogInfo(f"Found {total} images")
    if total == 0:
        log.LogInfo('Why are you even running this plugin?')
        return

    log.LogInfo('Start updating images (this might take a while)')
    count = 0
    for image in images:
        count += 1
        log.LogProgress(count/total)
        image_data = {
            'id': image.get('id'),
            'title': image.get('title')
        }
        if image.get('rating'):
            image_data['rating'] = image.get('rating')
        if image.get('studio'):
            image_data['studio_id'] = image.get('studio').get('id')
        if image.get('performers'):
            performer_ids = [p.get('id') for p in image.get('performers')]
            image_data['performer_ids'] = performer_ids
        if image.get('tags'):
            tag_ids = [t.get('id') for t in image.get('tags')]
            image_data['tag_ids'] = tag_ids
        if image.get('galleries'):
            gallery_ids = [g.get('id') for g in image.get('galleries')]
            image_data['gallery_ids'] = gallery_ids

        client.updateImage(image_data)

    log.LogInfo(f'Finished updating all {total} images')


main()
