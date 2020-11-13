from urllib.parse import urlsplit, urljoin, urlparse

import requests
import sys
import log


class StashInterface:
	port = ""
	url = ""
	headers = {
		"Accept-Encoding": "gzip, deflate, br",
		"Content-Type": "application/json",
		"Accept": "application/json",
		"Connection": "keep-alive",
		"DNT": "1"
	}
	cookies = {}

	def __init__(self, conn):
		self.port = conn['Port']
		scheme = conn['Scheme']

		# Session cookie for authentication
		self.cookies = {
			'session': conn.get('SessionCookie').get('Value')
		}

		domain = conn.get('Domain') if conn.get('Domain') else 'localhost'

		# Stash GraphQL endpoint
		self.url = scheme + "://" + domain + ":" + str(self.port) + "/graphql"

	def __callGraphQL(self, query, variables=None):
		json = {'query': query}
		if variables is not None:
			json['variables'] = variables

		response = requests.post(self.url, json=json, headers=self.headers, cookies=self.cookies)

		if response.status_code == 200:
			result = response.json()
			if result.get("error", None):
				for error in result["error"]["errors"]:
					raise Exception("GraphQL error: {}".format(error))
			if result.get("data", None):
				return result.get("data")
		elif response.status_code == 401:
			sys.exit("HTTP Error 401, Unauthorised. Cookie authentication most likely failed")
		else:
			raise Exception(
				"GraphQL query failed:{} - {}. Query: {}. Variables: {}".format(
					response.status_code, response.content, query, variables)
			)

	def findTagIdWithName(self, name):
		query = """
			query {
				allTags {
				id
				name
				}
			}
		"""

		result = self.__callGraphQL(query)

		for tag in result["allTags"]:
			if tag["name"] == name:
				return tag["id"]
		return None

	def createTagWithName(self, name):
		query = """
			mutation tagCreate($input:TagCreateInput!) {
				tagCreate(input: $input){
					id
				}
			}
		"""
		variables = {'input': {
			'name': name
		}}

		result = self.__callGraphQL(query, variables)
		return result["tagCreate"]["id"]

	def destroyTag(self, tag_id):
		query = """
			mutation tagDestroy($input: TagDestroyInput!) {
				tagDestroy(input: $input)
			}
		"""
		variables = {'input': {
			'id': tag_id
		}}

		self.__callGraphQL(query, variables)

	def getSceneById(self, scene_id):
		query = """
			query findScene($id: ID!) {
				findScene(id: $id) {
					id
					title
					details
					url
					date
					rating
					gallery {
						id
					}
					studio {
						id
					}
					tags {
						id
					}
					performers {
						id
					}
				}
			}
		"""

		variables = {
			"id": scene_id
		}

		result = self.__callGraphQL(query, variables)

		return result.get('findScene')

	def findRandomSceneId(self):
		query = """
			query findScenes($filter: FindFilterType!) {
				findScenes(filter: $filter) {
					count
					scenes {
						id
						tags {
							id
						}
					}
				}
			}
		"""

		variables = {'filter': {
			'per_page': 1,
			'sort': 'random'
		}}

		result = self.__callGraphQL(query, variables)

		if result["findScenes"]["count"] == 0:
			return None

		return result["findScenes"]["scenes"][0]

	# This method wipes rating, tags, performers, gallery and movie if omitted
	def updateScene(self, scene_data):
		query = """
			mutation sceneUpdate($input:SceneUpdateInput!) {
				sceneUpdate(input: $input) {
					id
				}
			}
		"""
		variables = {'input': scene_data}

		self.__callGraphQL(query, variables)

	def updateGallery(self, gallery_data):
		query = """
			mutation galleryUpdate($input: GalleryUpdateInput!) {
				galleryUpdate(input: $input) {
					id
				}
			}
		"""

		variables = {'input': gallery_data}

		self.__callGraphQL(query, variables)

	# Returns all scenes for the given regex
	def findScenesByPathRegex(self, regex):
		return self.__findScenesByPathRegex(regex)

	# Returns all scenes for the given regex
	# Searches all pages from given page on (default: 1)
	def __findScenesByPathRegex(self, regex, page=1):
		query = """
			query findScenesByPathRegex($filter: FindFilterType!) {
				findScenesByPathRegex(filter:$filter)  {
					count
					scenes {
						title
						id
						url
						rating
						gallery {id}
						studio {id}
						tags {id}
						performers {id}
					}
			}
		}
		"""

		variables = {
			"filter": {
				"q": regex,
				"per_page": 100,
				"page": page
			}
		}

		result = self.__callGraphQL(query, variables)
		log.LogDebug(f"Regex found {result.get('findScenesByPathRegex').get('count')} scene(s) on page {page}")

		scenes = result.get('findScenesByPathRegex').get('scenes')

		# If page is full, also scan next page:
		if len(scenes) == 100:
			next_page = self.__findScenesByPathRegex(regex, page + 1)
			for scene in next_page:
				scenes.append(scene)

		if page == 1:
			log.LogDebug(f"Regex found a total of {len(scenes)} scene(s)")
		return scenes

	def findGalleriesByTags(self, tag_ids):
		return self.__findGalleriesByTags(tag_ids)

	# Searches for galleries with given tags
	# Requires a list of tagIds
	def __findGalleriesByTags(self, tag_ids, page=1):
		query = """
		query findGalleriesByTags($tags: [ID!], $page: Int) {
			findGalleries(
				gallery_filter: { tags: { value: $tags, modifier: INCLUDES_ALL } }
				filter: { per_page: 100, page: $page }
			) {
				count
				galleries {
				id
				scene {
					id
				}
			}
		}
		}
		"""

		variables = {
			"tags": tag_ids,
			"page": page
		}

		result = self.__callGraphQL(query, variables)

		galleries = result.get('findGalleries').get('galleries')

		# If page is full, also scan next page(s) recursively:
		if len(galleries) == 100:
			log.LogDebug(f"Page {page} is full, also scanning next page")
			next_page = self.__findGalleriesByTags(tag_ids, page + 1)
			for gallery in next_page:
				galleries.append(gallery)

		return galleries

	def findScenesByTags(self, tag_ids):
		return self.__findScenesByTags(tag_ids)

	def __findScenesByTags(self, tag_ids, page=1):
		query = """
		query($tags: [ID!], $page: Int) {
			findScenes(
				scene_filter: { tags: { modifier: INCLUDES_ALL, value: $tags } }
				filter: { per_page: 1000, page: $page }
			) {
				count
				scenes {
					id
					url
				}
			}
		}
		"""

		variables = {
			"page": page,
			"tags": tag_ids
		}

		result = self.__callGraphQL(query, variables)
		scenes = result.get('findScenes').get('scenes')

		if len(scenes) == 1000:
			log.LogDebug(f"Page {page} is full, also scanning next page")
			next_page = self.__findGalleriesByTags(tag_ids, page + 1)
			for scene in next_page:
				scenes.append(scene)

		return scenes

	# Scrape
	def scrapeSceneURL(self, url):
		query = """
		query($url: String!) {
			scrapeSceneURL(url: $url) {
				title
				details
				date
				url
				tags {
					name
					stored_id
				}
				studio {
					name
					stored_id
				}
				performers {
					name
					stored_id
				}
				image
			}
		}
		"""

		variables = {
			'url': url
		}

		result = self.__callGraphQL(query, variables)
		return result.get('scrapeSceneURL')

	def createStudio(self, name, url=None):
		query = """
			mutation($name: String!, $url: String) {
				studioCreate(input: { name: $name, url: $url }) {
					id
				}
			}
		"""
		variables = {
			'name': name,
			'url': url
		}

		result = self.__callGraphQL(query, variables)
		return result.get("studioCreate").get("id")

	def createPerformerByName(self, name):
		query = """
			mutation($name: String!) {
				performerCreate(input: { name: $name }) {
					id
				}
			}
		"""

		variables = {
			'name': name
		}

		result = self.__callGraphQL(query, variables)
		return result.get('performerCreate').get('id')

	def findMovieByName(self, name):
		query = "query {allMovies {id name aliases date rating studio {id name} director synopsis}}"

		response = self.__callGraphQL(query)

		for movie in response.get('allMovies'):
			if movie.get('name') == name:
				return movie
		return None
