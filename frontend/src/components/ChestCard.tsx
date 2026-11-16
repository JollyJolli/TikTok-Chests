import { Clock3, ExternalLink, Eye, Heart, Trophy, Users, Zap } from 'lucide-react'
import { memo } from 'react'
import type { Chest } from '../types'
import { formatCountdown, remainingSeconds } from '../utils/radar'

interface Props { chest: Chest; favorite: boolean; now: number; onFavorite: () => void }
const metric = (value: number | null | undefined) => value === null || value === undefined ? '—' : new Intl.NumberFormat().format(value)
export const ChestCard = memo(function ChestCard({ chest, favorite, now, onFavorite }: Props) {
  const countdown = formatCountdown(remainingSeconds(chest, now)); const initial = (chest.streamer_display_name || chest.streamer_username).slice(0,1).toUpperCase()
  return <article className="chest-card">
    <div className="card-top"><div className="creator"><div className="avatar">{chest.avatar_url ? <img src={chest.avatar_url} alt="" referrerPolicy="no-referrer"/> : initial}<span/></div><div><h3>{chest.streamer_display_name || `@${chest.streamer_username}`}</h3><p>@{chest.streamer_username}</p></div></div>
      <button className="icon-button" onClick={onFavorite} aria-label={favorite ? 'Remove favorite' : 'Add favorite'} aria-pressed={favorite}><Heart size={18} fill={favorite ? 'currentColor' : 'none'}/></button></div>
    <div className="reward"><span><Zap size={17}/> {metric(chest.coins)} <small>coins</small></span><strong className="score">{chest.opportunity_score === null ? 'Unscored' : `${Math.round(chest.opportunity_score)} score`}</strong></div>
    <div className="metrics">
      <div><Trophy/><span>Winners</span><b>{metric(chest.winners)}</b></div><div><Zap/><span>Per winner</span><b>{metric(chest.coins_per_winner)}</b></div><div><Eye/><span>Viewers</span><b>{metric(chest.viewer_count)}</b></div><div><Users/><span>Participants</span><b>{metric(chest.participants)}</b></div>
    </div>
    <div className="card-bottom"><span className={`countdown ${countdown === 'Open now' ? 'open' : ''}`}><Clock3 size={16}/>{countdown}</span><a className="live-button" href={chest.live_url} target="_blank" rel="noopener noreferrer">Open LIVE <ExternalLink size={15}/></a></div>
    <p className="heuristic">Opportunity score is a heuristic, not a win probability. Rewards are claimed manually on TikTok.</p>
  </article>
})
