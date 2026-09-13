const API = import.meta.env.VITE_API_URL || '/api'

export function api(path, options = {}) {
  const token = localStorage.token
  return fetch(API + path, { headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }, ...options }).then(async response => {
    const result = await response.json()
    if (!response.ok) throw Error(result.detail || 'Something went wrong')
    return result
  })
}