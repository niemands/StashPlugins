# StashPlugins
A collection of python plugins for stash

### Currently available plugins:

Plugin config           | Description                                         | Notes
----------------------- | --------------------------------------------------- | --------
set_ph_urls.yml         | Add urls to pornhub scenes downloaded by Youtube-dl |
gallerytags.yml         | Copy information from attached scene to galleries   |
bulk_url_scraper.yml    | Bulk scene url scraping                             | Config (/py_plugins/config.py) has to be edited manually, until plugin parameters get implemented
update_image_titles.yml | Update all image titles (Fixes natural sort)        |
    
### Download instructions:
Drop the py_plugins folder as well as all desired plugin configurations in stash's plugin folder
and press the `Reload plugins` button in the Plugin settings

All plugins require python 3, as well as the requests module, which can be installed with the command `pip install requests`.
If the python installation requires you to call python via `python3`, you have to change python to python3 in the exec block of each plugin config.
