instagram-atom
=============

_Closed to new users. Instagram is interpreting this as a bot and disabling people's accounts, including mine, when they use it. Ugh. ☹️_

A webapp that generates and serves an Atom feed of your Instagram feed, ie
photos from people you follow.

Deployed on App Engine at https://instagram-atom.appspot.com/

License: This project is placed in the public domain.


Development
---
1. Fork and clone this repo.
1. `pip install -r requirements.txt`, optionally in a virtualenv.
1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/) with the `gcloud-appengine-python` and `gcloud-appengine-python-extras` [components](https://cloud.google.com/sdk/docs/components#additional_components).
1. `GAE_ENV=localdev FLASK_ENV=development FLASK_APP=main.py flask run -p 8080`

To release a new version of the browser extension, [follow the Bridgy browser extension release notes](https://github.com/snarfed/bridgy/#browser-extension-release).


Browser extension: Changelog
---

0.1, 2022-12-03

* Initial release!


