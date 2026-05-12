const getBackendBaseUrl = () => {
  return (
    Netlify.env.get('BACKEND_API_URL') ||
    Netlify.env.get('NETLIFY_BACKEND_API_URL') ||
    Netlify.env.get('VITE_API_URL') ||
    ''
  ).replace(/\/$/, '')
}

export default async () => {
  const backendBaseUrl = getBackendBaseUrl()

  if (!backendBaseUrl) {
    console.log('Menu refresh skipped: BACKEND_API_URL is not configured')
    return
  }

  const response = await fetch(`${backendBaseUrl}/api/menus/refresh-async`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
    },
  })

  if (!response.ok) {
    console.log(`Menu refresh trigger failed: ${response.status} ${response.statusText}`)
    return
  }

  console.log('Menu refresh trigger succeeded')
}

export const config = {
  schedule: '0 */1 * * *',
}
