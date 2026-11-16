import { useCallback, useEffect, useRef, useState } from 'react'
import type { Chest, Snapshot, Stats, StreamState } from '../types'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'
const emptyStats: Stats = { monitored_streams:0, connected_streams:0, queued_streams:0, active_chests:0, expired_chests:0, detected_total:0, events_received:0, connection_errors:0, websocket_clients:0, last_update_at:null, last_discovery_at:null, discovery_mode:'manual', discovery_available:false, discovery_message:'Waiting for backend status…', demo_mode:false }

export function useRadar(onNewChest?: (chest: Chest) => void) {
  const [chests, setChests] = useState<Chest[]>([]); const [streams, setStreams] = useState<StreamState[]>([])
  const [stats, setStats] = useState<Stats>(emptyStats); const [connection, setConnection] = useState<'connecting'|'connected'|'reconnecting'|'offline'>('connecting')
  const [error, setError] = useState<string | null>(null); const callback = useRef(onNewChest)
  useEffect(() => { callback.current = onNewChest }, [onNewChest])
  useEffect(() => {
    let socket: WebSocket | undefined; let timer: number | undefined; let stopped = false; let retries = 0
    const connect = () => {
      setConnection(retries ? 'reconnecting' : 'connecting'); socket = new WebSocket(WS)
      socket.onopen = () => { retries = 0; setConnection('connected'); setError(null) }
      socket.onmessage = (event) => { try {
        const message = JSON.parse(event.data)
        if (message.type === 'snapshot') { const data = message.data as Snapshot; setChests(data.chests); setStreams(data.streams); setStats(data.stats) }
        else if (message.type === 'chest.created') { const chest = message.data as Chest; setChests((items) => [...items.filter((item) => item.id !== chest.id), chest]); callback.current?.(chest) }
        else if (message.type === 'chest.updated') { const chest = message.data as Chest; setChests((items) => [...items.filter((item) => item.id !== chest.id), chest]) }
        else if (message.type === 'chest.expired') setChests((items) => items.filter((item) => item.id !== message.data.id))
        else if (message.type === 'stream.updated') { const stream = message.data as StreamState; setStreams((items) => [...items.filter((item) => item.username !== stream.username), stream]) }
        else if (message.type === 'stats.updated') setStats(message.data as Stats)
      } catch { setError('The backend sent an unreadable update.') } }
      socket.onclose = () => { if (!stopped) { setConnection('reconnecting'); retries += 1; timer = window.setTimeout(connect, Math.min(1000 * 2 ** retries, 30000)) } }
      socket.onerror = () => { setError('Cannot reach the radar backend.'); socket?.close() }
    }
    connect(); return () => { stopped = true; if (timer) clearTimeout(timer); socket?.close() }
  }, [])
  const addStream = useCallback(async (value: string) => { const response = await fetch(`${API}/api/streams`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({value}) }); const body = await response.json().catch(() => ({})); if (!response.ok) throw new Error(body.detail || 'Could not add stream'); return body }, [])
  const removeStream = useCallback(async (username: string) => { const response = await fetch(`${API}/api/streams/${encodeURIComponent(username)}`, { method:'DELETE' }); if (!response.ok && response.status !== 204) throw new Error('Could not remove stream') }, [])
  return { chests, streams, stats, connection, error, addStream, removeStream }
}
