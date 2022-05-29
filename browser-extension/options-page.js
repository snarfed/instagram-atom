'use strict'

import './browser-polyfill.js'

import {Instagram} from './instagram.js'
import {
  pollNow,
  update,
} from './options.js'

document.addEventListener('DOMContentLoaded', function () {
  document.querySelector('#poll').addEventListener('click', () => pollNow(Instagram))

  console.debug('Scheduling options page refresh every minute')
  browser.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name == 'options-page-refresh') {
      update()
    }
  })
  browser.alarms.create('options-page-refresh', {
    periodInMinutes: 1,
  })
  update()
})
