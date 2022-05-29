'use strict'

const IA_BASE_URL = 'https://instagram-atom.appspot.com'
// const IA_BASE_URL = 'http://localhost:8080'


/*
 * Initial setup: generate a token.
 */
async function generateToken(force) {
  let token = (await browser.storage.sync.get(['token'])).token
  if (!token) {
    token = Math.random().toString(36).substring(2, 15)
    await browser.storage.sync.set({token: token})
    console.log(`Generated new token: ${token}.`)
  }
}


/**
 * Abstract base class for a silo, eg Facebook or Instagram.
 *
 * See below class declaration for class static properties.
 */
class Silo {
  /**
   * Returns the URL path to the feed of posts.
   *
   * To be implemented by subclasses.
   *
   * @returns {String} URL path
   */
  static feedPath() {
    throw new Error('Not implemented')
  }

  /**
   * Returns HTTP headers to include in silo requests.
   *
   * Defaults to none. Optional, only implement for silos that need specific headers.
   */
  static headers() {
    return {}
  }

  /**
   * Fetches the user's Instagram feed and forwards to instagram-atom.
   */
  static async poll() {
    const token = (await browser.storage.sync.get(['token'])).token
    if (!token) {
      return
    }

    console.log('Starting poll...')
    await this.storageSet('lastStart', Date.now())

    const data = await this.siloGet(this.feedPath())
    if (data) {
      if (await this.postIA('/feed/store', data)) {
        await this.storageSet('lastSuccess', Date.now())
        await this.storageSet('lastError', null)
      }
    }

    console.log('Done!')
  }

  /**
   * Finds and returns session cookies for this silo.
   *
   * Looks through all cookie stores and contextual identities (ie containers).
   *
   * TODO: debug why this still doesn't actually work with eg the Firefox
   * Container Tabs extension. The HTTP requests complain that the session
   * cookie is expired, even if it works in the container tab.
   *
   * @returns {String} Cookie header for the silo, ready to be sent, or null
   */
  static async findCookies(path) {
    // getAllCookieStores() only returns containers with open tabs, so we have to
    // use the contextualIdentities API to get any others, eg Firefox container tabs.
    // https://bugzilla.mozilla.org/show_bug.cgi?id=1486274
    let storeIds = (await browser.cookies.getAllCookieStores()).map(s => s.id)

    // this needs the contextualIdentities permission, which we don't currently
    // include in manifest.json since it's not supported in Chrome.
    if (browser.contextualIdentities) {
        storeIds = storeIds.concat(
          (await browser.contextualIdentities.query({})).map(s => s.cookieStoreId))
    }

    if (storeIds.find(id => id.startsWith('firefox-container-'))) {
      console.debug('Detected active Firefox Container add-on!')
    }

    for (const storeId of storeIds) {
      const cookies = await browser.cookies.getAll({
        storeId: storeId,
        domain: this.DOMAIN,
      })
      if (cookies) {
        const header = cookies.map(c => `${c.name}=${c.value}`).join('; ')
        // console.debug(header)
        if (header.includes(`${this.COOKIE}=`)) {
          console.debug(`Using ${this.NAME} cookie ${header}`)
          return header
        }
      }
    }

    console.log(`No ${this.NAME} ${this.COOKIE} cookie found!`)
  }

  /**
   * WebRequest onBeforeSendHeaders listener that injects cookies.
   *
   * Needed to support Firefox container tabs.
   *
   * https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/webRequest/onBeforeSendHeaders
   */
  static injectCookies(cookies) {
    return function (details) {
      for (let header of details.requestHeaders) {
        if (header.name == 'X-Instagram-Atom') {
          header.name = 'Cookie'
          header.value = cookies
          return details
        }
      }
    }
  }

  /**
   * Makes an HTTP GET request to the silo.
   *
   * @param {String} url
   * @returns {String} Response body from the silo
   */
  static async siloGet(url) {
    // Set up cookies. Can't pass them to fetch directly because it blocks the
    // Cookie header. :( Instead, we use webRequest, which lets us.
    // https://developer.mozilla.org/en-US/docs/Glossary/Forbidden_header_name
    // https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/webRequest/onBeforeSendHeaders
    //
    // (If only the fetch API let us specify a cookie store, we could skip all
    // this and just let it automatically send the appropriate cookies from that
    // store. We already have the contextualIdentities permission, so we already
    // have access to those cookies. Maybe because contextualIdentities isn't a
    // cross-browser standard yet? Argh!)
    const cookies = await this.findCookies()
    if (!cookies) {
      await this.recordError(`Not logged into ${this.NAME}`)
      return
    }

    const inject = this.injectCookies(cookies)
    if (!browser.webRequest.onBeforeSendHeaders.hasListener(inject)) {
      browser.webRequest.onBeforeSendHeaders.addListener(
        inject,
        {urls: [`*://*.${this.DOMAIN}/*`]},
        ['blocking', 'requestHeaders']
      );
    }

    // check if url is a full URL or a path
    try {
      const parsed = new URL(url)
      if (parsed.hostname != this.DOMAIN &&
          !parsed.hostname.endsWith(`.${this.DOMAIN}`)) {
        await this.recordError(`Got non-${this.NAME} URL: ${url}`)
        return
      }
    } catch (err) {
      url = `${this.BASE_URL}${url}`
    }

    // Make HTTP request
    console.debug(`Fetching ${url}`)
    const headers = {'X-Instagram-Atom': '1'}
    Object.assign(headers, this.headers())
    const res = await fetch(url, {
      method: 'GET',
      redirect: 'follow',
      // replaced in injectCookies()
      headers: headers,
    })

    if (res.redirected) {
      console.warn(`Got redirected! Final URL: ${res.url}`)
    }

    console.debug(`Got ${res.status}`)
    const text = await res.text()
    console.debug(text)
    if (res.ok) {
      return text
    }
  }

  /**
   * Makes an HTTP POST request to instagram-atom.
   *
   * @param {String} path_query
   * @param {String} body
   * @returns {Object} JSON parsed response from instagram-atom
   */
  static async postIA(path_query, body) {
    const token = (await browser.storage.sync.get(['token'])).token
    if (!token) {
      await this.recordError('No stored token!')
      return
    }

    let url = new URL(`${IA_BASE_URL}/feed/store`)
    url.searchParams.set('token', token)

    console.debug(`Sending to ${url}`)
    try {
      // TODO: support optional timeout via signal and AbortHandler
      // https://dmitripavlutin.com/timeout-fetch-request/
      const res = await fetch(url.toString(), {
        method: 'POST',
        body: body,
      })
      console.debug(`Got ${res.status}`)
      if (res.ok) {
        let json = await res.json()
        console.debug(json)
        return json
      } else {
        await this.recordError(await res.text())
      }
    } catch (err) {
      await this.recordError(err)
      return null
    }
  }

  /**
   * Logs an error to the console and stores it in lastError.
   *
   * @param {String} msg
   */
  static async recordError(msg) {
    console.warn(msg)
    await this.storageSet('lastError', msg)
  }

  /**
   * Fetches a value from local storage for a key prefixed with this silo's name.
   *
   * For example, storageGet('foo') would return the value for key 'NAME-foo'.
   *
   * @param {String} key
   * @returns {Object} stored value, or none
   */
  static async storageGet(key) {
    return (await browser.storage.local.get([key]))[key]
  }

  /**
   * Stores a value from local storage for a key prefixed with this silo's name.
   *
   * For example, storageSet('foo') would store the value for key 'NAME-foo'.
   *
   * @param {String} key
   * @param {Object} value
   */
  static async storageSet(key, value) {
    return await browser.storage.local.set({[key]: value})
  }

  /**
   * Returns the name of the poll alarm for this silo.
   *
   * @returns {String} alarm name
   */
  static alarmName() {
    return 'instagram-atom-poll'
  }
}

Silo.DOMAIN = null     // eg 'silo.com'
Silo.NAME = null       // eg 'instagram'
Silo.BASE_URL = null   // eg 'https://silo.com'
Silo.LOGIN_URL = null  // eg 'https://silo.com/login'
Silo.COOKIE = null     // eg 'sessionid'


export {
  IA_BASE_URL,
  generateToken,
  Silo,
}
