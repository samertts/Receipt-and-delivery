let accessToken = ''
let refreshToken = ''
let user = null

export function setSession({ accessToken: newAccessToken = '', refreshToken: newRefreshToken = '', user: newUser = null } = {}) {
  accessToken = newAccessToken
  refreshToken = newRefreshToken
  user = newUser
}

export function updateAccessToken(newAccessToken = '') {
  accessToken = newAccessToken
}

export function updateRefreshToken(newRefreshToken = '') {
  refreshToken = newRefreshToken
}

export function getAccessToken() {
  return accessToken
}

export function getRefreshToken() {
  return refreshToken
}

export function getSessionUser() {
  return user
}

export function clearSession() {
  accessToken = ''
  refreshToken = ''
  user = null
}
