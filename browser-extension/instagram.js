'use strict'

import {Silo} from './common.js'


class Instagram extends Silo {
  /** See below class declaration for class static properties. */

  /**
   * Returns the URL path to the feed of posts.
   */
  static feedPath() {
    return '/api/v1/feed/timeline/'
  }

  /**
   * Returns HTTP headers to include in silo requests.
   */
  static headers() {
    return {
      // duplicated in granary/instagram.py
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:96.0) Gecko/20100101 Firefox/96.0',
      'X-IG-App-ID': '936619743392459',  // desktop web
    }
  }
}

Instagram.DOMAIN = 'instagram.com'
Instagram.NAME = 'instagram'
Instagram.BASE_URL = 'https://i.instagram.com'
Instagram.LOGIN_URL = `https://www.instagram.com/accounts/login/`
Instagram.COOKIE = 'sessionid'

export {
  Instagram,
}
