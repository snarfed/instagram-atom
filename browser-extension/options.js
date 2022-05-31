'use strict'

import './browser-polyfill.js'

import {
  IA_BASE_URL,
} from './common.js'

import {Instagram} from './instagram.js'


async function update() {
  console.debug('Updating options page UI')

  const token = (await browser.storage.sync.get()).token
  document.querySelector(`#feedUrl`).value = `${IA_BASE_URL}/feed?token=${token}`

  const data = await browser.storage.local.get()
  for (const silo of [Instagram]) {
    const lastStart = data[`lastStart`]
    if (lastStart) {
      const date = new Date(lastStart).toLocaleString()
      document.getElementById(`lastStart`).innerText = date
    }

    const lastSuccess = data[`lastSuccess`]
    if (lastSuccess) {
      const date = new Date(lastSuccess).toLocaleString()
      document.getElementById(`lastSuccess`).innerText = date
    }

    const cookies = await silo.findCookies()
    let status = document.querySelector(`#status`)
    const lastError = data[`lastError`]
    if (!cookies) {
      status.innerHTML = `No ${silo.DOMAIN} cookie found. <a href="${silo.LOGIN_URL}" target="_blank">Try logging in!</a>`
      status.className = 'error'
    } else if (!lastStart) {
      status.innerHTML = 'Not started yet'
      status.className = 'pending'
    } else if (lastSuccess >= lastStart || !lastError) {
      status.innerHTML = 'OK'
      status.className = 'ok'
    } else if (lastStart > Date.now() - 1 * 60 * 1000) {
      status.innerHTML = 'Polling now...'
      status.className = 'pending'
    } else if (!lastSuccess) {
      status.innerHTML = 'Initial poll did not succeed'
      if (lastError) {
        status.innerHTML += `: ${lastError}`
      }
      status.className = 'error'
    } else if (lastStart > lastSuccess) {
      status.innerHTML = `Last poll did not succeed: ${lastError}`
      if (lastError) {
        status.innerHTML += `: ${lastError}`
      }
      // want to include this but can't get it to work. Firefox says
      // "Uncaught SyntaxError: private fields are not currently supported"
      // '<a href="#" onclick="document.querySelector('#poll').click()">Retry now!</a>
      status.className = 'error'
    }
  }

  const username = data['username']
  if (username) {
    document.querySelector('#username').innerText = username
    document.querySelector('#username').href = `https://www.instagram.com/${username}/`
  }
}

function pollNow(silo) {
  let status = document.querySelector(`#status`)
  status.innerHTML = 'Polling now...'
  status.className = 'pending'
  silo.poll().then(update)
}

export {
  pollNow,
  update,
}
