import type { Chest, Filters, SortKey } from '../types'

export const defaultFilters: Filters = { search: '', minCoins: 0, maxViewers: 0, minWinners: 0, minCoinsPerWinner: 0, maxMinutes: 0, rewardType: '', region: '', favoritesOnly: false }

export function remainingSeconds(chest: Chest, now = Date.now()): number | null {
  return chest.opens_at ? Math.max(0, Math.ceil((new Date(chest.opens_at).getTime() - now) / 1000)) : null
}
export function formatCountdown(seconds: number | null): string {
  if (seconds === null) return 'Time unavailable'
  if (seconds <= 0) return 'Open now'
  const minutes = Math.floor(seconds / 60); const rest = seconds % 60
  return `${minutes}:${String(rest).padStart(2, '0')}`
}
export function filterChests(chests: Chest[], filters: Filters, favorites: string[], now = Date.now()): Chest[] {
  const query = filters.search.trim().toLowerCase()
  return chests.filter((chest) => {
    const remaining = remainingSeconds(chest, now)
    return chest.status !== 'expired' && (!query || chest.streamer_username.toLowerCase().includes(query) || chest.streamer_display_name?.toLowerCase().includes(query))
      && (!filters.minCoins || (chest.coins ?? -1) >= filters.minCoins)
      && (!filters.maxViewers || (chest.viewer_count ?? Infinity) <= filters.maxViewers)
      && (!filters.minWinners || (chest.winners ?? -1) >= filters.minWinners)
      && (!filters.minCoinsPerWinner || (chest.coins_per_winner ?? -1) >= filters.minCoinsPerWinner)
      && (!filters.maxMinutes || remaining !== null && remaining <= filters.maxMinutes * 60)
      && (!filters.rewardType || chest.reward_type === filters.rewardType)
      && (!filters.region || chest.region === filters.region)
      && (!filters.favoritesOnly || favorites.includes(chest.streamer_username))
  })
}
export function sortChests(chests: Chest[], key: SortKey): Chest[] {
  const value = (chest: Chest) => ({ recommended: chest.opportunity_score ?? -1, coins: chest.coins ?? -1, cpw: chest.coins_per_winner ?? -1, viewers: -(chest.viewer_count ?? Infinity), winners: chest.winners ?? -1, opening: -(chest.opens_at ? new Date(chest.opens_at).getTime() : Infinity), recent: new Date(chest.detected_at).getTime() }[key])
  return [...chests].sort((a, b) => value(b) - value(a))
}
