'use strict'

import {
  IA_BASE_URL,
} from '../common.js'

import {
  Instagram,
} from '../instagram.js'

import './testutil.js'

beforeEach(() => {
  browser.storage.local.data = {}
  browser.cookies.getAll.mockResolvedValue([
    {name: 'sessionid', value: 'foo'},
    {name: 'bar', value: 'baz'},
])
})

test('poll', async () => {
  const start = Date.now()

  fetch.mockResponseOnce('fake feed')
  fetch.mockResponseOnce('"OK"')
  await Instagram.poll()
  expect(fetch.mock.calls.length).toBe(2)

  const end = Date.now()

  for (const field of ['lastStart', 'lastSuccess']) {
    const timestamp = await Instagram.storageGet(field)
    expect(timestamp).toBeGreaterThanOrEqual(start)
    expect(timestamp).toBeLessThanOrEqual(end)
  }
  expect(await Instagram.storageGet('lastSuccess')).toBeGreaterThanOrEqual(
    await Instagram.storageGet('lastStart'))

  expect(fetch.mock.calls[0][0]).toBe('https://i.instagram.com/api/v1/feed/timeline/')
  expect(fetch.mock.calls[1][0]).toBe(`${IA_BASE_URL}/feed/store?token=towkin`)
  expect(fetch.mock.calls[1][1].body).toBe('fake feed')
})

test('poll, no stored token', async () => {
  // no token stored
  browser.storage.sync.data = {}
  await Instagram.poll()

  expect(fetch.mock.calls.length).toBe(0)
  expect(browser.storage.local.data['lastStart']).toBeUndefined()
  expect(browser.storage.local.data['lastSuccess']).toBeUndefined()
  expect(browser.alarms.alarms).toEqual({})
})

test('poll, feed error', async () => {
  fetch.mockResponseOnce('air-roar', {status: 400})  // Instagram returns an HTTP error
  await Instagram.poll()

  expect(fetch.mock.calls.length).toBe(1)
  expect(browser.storage.local.data['lastStart']).toBeDefined()
  expect(browser.storage.local.data['lastSuccess']).toBeUndefined()
})

test('poll, IA error', async () => {
  fetch.mockResponseOnce('fake feed')
  fetch.mockResponseOnce('air-roar', {status: 400})  // IA returns an HTTP error
  await Instagram.poll()

  expect(fetch.mock.calls.length).toBe(2)
  expect(browser.storage.local.data['lastStart']).toBeDefined()
  expect(browser.storage.local.data['lastSuccess']).toBeUndefined()
  expect(browser.storage.local.data['lastError']).toEqual('air-roar')
})
