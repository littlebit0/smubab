import { getStore } from '@netlify/blobs'

const getBackendBaseUrl = () => {
  return (
    Netlify.env.get('BACKEND_API_URL') ||
    Netlify.env.get('NETLIFY_BACKEND_API_URL') ||
    Netlify.env.get('VITE_API_URL') ||
    ''
  ).replace(/\/$/, '')
}

const fetchJson = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`)
  }

  return response.json()
}

const hasTodayMenus = payload =>
  payload?.success && Array.isArray(payload.menus) && payload.menus.length > 0

const hasWeeklyMenus = payload =>
  payload?.success && Array.isArray(payload.data) && payload.data.length > 0

export default async () => {
  const backendBaseUrl = getBackendBaseUrl()

  if (!backendBaseUrl) {
    console.log('Menu refresh skipped: BACKEND_API_URL is not configured')
    return
  }

  const store = getStore('menu-snapshots')

  try {
    const [todayPayload, weekPayload] = await Promise.all([
      fetchJson(`${backendBaseUrl}/api/menus/today`),
      fetchJson(`${backendBaseUrl}/api/menus/week`),
    ])

    if (hasTodayMenus(todayPayload)) {
      await store.set('today.json', JSON.stringify(todayPayload))
      console.log(`Today menu snapshot updated: ${todayPayload.menus.length} menus`)
    }

    if (hasWeeklyMenus(weekPayload)) {
      await store.set('week.json', JSON.stringify(weekPayload))
      console.log(`Weekly menu snapshot updated: ${weekPayload.data.length} menus`)
    }

    if (hasTodayMenus(todayPayload) && hasWeeklyMenus(weekPayload)) {
      return
    }
  } catch (error) {
    console.log(`Menu snapshot read failed: ${error.message}`)
  }

  try {
    await fetchJson(`${backendBaseUrl}/api/menus/refresh-async`, { method: 'POST' })
    console.log('Menu refresh trigger succeeded')
  } catch (error) {
    console.log(`Menu refresh trigger failed: ${error.message}`)
  }
}

export const config = {
  schedule: '*/10 * * * *',
}
