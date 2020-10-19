import os
import json
import sys
import log
from stash_interface import StashInterface

def main():
    input = readJSONInput()
    #log.LogDebug(json.dumps(input))

    client = StashInterface(input.get('server_connection'))
    add_ph_urls(client)

    output = {
        'output': 'ok'
    }

    print(json.dumps(output) + '\n')

def readJSONInput():
    input = sys.stdin.read()
    return json.loads(input)

def add_ph_urls(client):
    count = 0

    scenes = client.findScenesByPathRegex(
        r"-ph[a-z0-9]{13}\.(?:[mM][pP]4|[wW][mM][vV])$"
    )

    for scene in scenes:
        if scene.get('url') == None or scene.get('url') == "":
            ph_id = os.path.splitext(scene.get('title').split('-ph')[1])[0]
            stash_id = scene.get('id')
            url = f"https://www.pornhub.com/view_video.php?viewkey=ph{ph_id}"

            sceneData = {
                'id': scene.get('id'),
                'url': url
            }

            # Required, would be cleared otherwise
            if scene.get('rating') != None:
                sceneData['rating'] = scene.get('rating')

            tagIds = []
            for t in scene.get('tags'):
                tagIds.append(t.get('id'))
            sceneData['tag_ids'] = tagIds

            performerIds = []
            for p in scene.get('performers'):
                performerIds.append(p.get('id'))
            sceneData['performer_ids'] = performerIds

            if scene.get('studio') != None:
                sceneData['studio_id'] = scene.get('studio').get('id')

            if scene.get('gallery') != None:
                sceneData['gallery_id'] = scene.get('gallery').get('id')

            client.updateScene(sceneData)
            log.LogDebug(f'Set url for scene {scene.get("id")}')
            count += 1

    log.LogInfo(f"Set urls for {count} scene(s)")


main()
