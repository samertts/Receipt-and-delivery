// Browser authentication uses HttpOnly cookies. This module keeps only a
// minimal in-memory profile for UI state and intentionally never stores tokens.
let user = null

export function setSession({ user: newUser = null } = {}) {
  user = newUser
}

export function updateAccessToken(_newAccessToken = '') {}

export function updateRefreshToken(_newRefreshToken = '') {}

export function getAccessToken() {
  return ''
}

export function getRefreshToken() {
  return ''
}

export function getSessionUser() {
  return user
}

export function clearSession() {
  user = null
}
