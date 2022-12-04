import './browser-polyfill.js'

import {generateToken} from './common.js'
import {Instagram} from './instagram.js'

/* Local storage schema for this extension:
 *
 * browser.storage.sync:
 *   token: [string]
 *
 * browser.storage.local:
 *   lastStart: [Date]
 *   lastSuccess: [Date]
 *   lastError: [string]
 */

const FREQUENCY_MIN = 30

// Must be top level in non-persistent background (aka event) pages
// https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Background_scripts#move_event_listeners
browser.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name == Instagram.alarmName()) {
    Instagram.poll()
  }
})

function schedulePoll() {
  for (const silo of [Instagram]) {
    const name = silo.alarmName()
    browser.alarms.get(name).then(function(alarm) {
      if (!alarm) {
        console.log(`Scheduling ${silo.NAME} poll every ${FREQUENCY_MIN}m`)
        browser.alarms.create(name, {
          delayInMinutes: FREQUENCY_MIN,
          periodInMinutes: FREQUENCY_MIN,
        })
      }
    })
  }
}

generateToken().then((generated) => {
  if (generated) {
    Instagram.poll()
  }
  schedulePoll()
})
