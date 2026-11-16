export type ChestStatus = 'upcoming' | 'open' | 'expired'
export type ConnectionStatus = 'queued' | 'connecting' | 'connected' | 'reconnecting' | 'offline' | 'error' | 'stopped'

export interface Chest {
  id: string; streamer_username: string; streamer_display_name: string | null; avatar_url: string | null;
  room_id: string | null; live_url: string; coins: number | null; winners: number | null;
  coins_per_winner: number | null; opportunity_score: number | null; reward_type: string | null;
  opens_at: string | null; expires_at: string | null; chest_type: string | null; region: string | null;
  participants: number | null; viewer_count: number | null; detected_at: string; updated_at: string;
  status: ChestStatus; source: 'live' | 'demo'
}
export interface StreamState { username: string; display_name: string | null; viewer_count: number | null; status: ConnectionStatus; source: string; last_error: string | null }
export interface Stats { monitored_streams: number; connected_streams: number; queued_streams: number; active_chests: number; expired_chests: number; detected_total: number; events_received: number; connection_errors: number; websocket_clients: number; last_update_at: string | null; last_discovery_at: string | null; discovery_mode: 'manual'|'automatic'|'demo'; discovery_available: boolean; discovery_message: string; demo_mode: boolean }
export interface Snapshot { chests: Chest[]; streams: StreamState[]; stats: Stats; sequence: number }
export interface Filters { search: string; minCoins: number; maxViewers: number; minWinners: number; minCoinsPerWinner: number; maxMinutes: number; rewardType: string; region: string; favoritesOnly: boolean }
export type SortKey = 'recommended'|'coins'|'cpw'|'viewers'|'winners'|'opening'|'recent'
export interface Preferences { favorites: string[]; sort: SortKey; filters: Filters; notifications: boolean; favoriteNotifications: boolean; openingNotifications: boolean; sound: boolean; coinThreshold: number }
