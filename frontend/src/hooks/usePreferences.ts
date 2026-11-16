import { useCallback, useState } from 'react'
import type { Preferences } from '../types'
import { defaultFilters } from '../utils/radar'

const KEY = 'tiktok-chests.preferences.v1'
export const defaults: Preferences = { favorites: [], sort: 'recommended', filters: defaultFilters, notifications: false, favoriteNotifications: true, openingNotifications: false, sound: false, coinThreshold: 0 }
function load(): Preferences {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) || '{}')
    return { ...defaults, ...saved, filters: { ...defaultFilters, ...(saved.filters || {}) } }
  } catch {
    return defaults
  }
}
export function usePreferences() {
  const [preferences, setState] = useState<Preferences>(load)
  const setPreferences = useCallback((next: Preferences | ((value: Preferences) => Preferences)) => setState((current) => { const value = typeof next === 'function' ? next(current) : next; localStorage.setItem(KEY, JSON.stringify(value)); return value }), [])
  const reset = useCallback(() => { localStorage.removeItem(KEY); setState(defaults) }, [])
  return { preferences, setPreferences, reset }
}
