import { Bell, Boxes, CircleHelp, Coins, Heart, Radio, Settings, ShieldCheck, Signal, WifiOff, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { ChestCard } from './components/ChestCard'
import { Filters } from './components/Filters'
import { Logo } from './components/Logo'
import { MonitorPanel } from './components/MonitorPanel'
import { usePreferences, defaults } from './hooks/usePreferences'
import { useRadar } from './hooks/useRadar'
import type { Chest } from './types'
import { filterChests, sortChests } from './utils/radar'

const INITIAL_NOW = Date.now()

function App() {
  const { preferences, setPreferences, reset } = usePreferences(); const prefsRef = useRef(preferences)
  useEffect(() => { prefsRef.current = preferences }, [preferences])
  const notify = (chest: Chest) => { const p=prefsRef.current; if(!p.notifications || chest.source==='demo' || (chest.coins??0)<p.coinThreshold || (p.favoriteNotifications && !p.favorites.includes(chest.streamer_username))) return; if(Notification.permission==='granted') new Notification('Treasure Box detected',{body:`@${chest.streamer_username} · ${chest.coins??'Unknown'} coins`,tag:`chest-${chest.id}`}) }
  const {chests,streams,stats,connection,error,addStream,removeStream}=useRadar(notify); const [now,setNow]=useState(INITIAL_NOW); const [settingsOpen,setSettingsOpen]=useState(false)
  useEffect(()=>{const timer=window.setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(timer)},[])
  const visible=useMemo(()=>sortChests(filterChests(chests,preferences.filters,preferences.favorites,now),preferences.sort),[chests,preferences,now])
  const totalCoins=chests.reduce((sum,chest)=>sum+(chest.status!=='expired'?(chest.coins??0):0),0)
  const regions=[...new Set(chests.map(c=>c.region).filter((v):v is string=>Boolean(v)))]; const rewards=[...new Set(chests.map(c=>c.reward_type).filter((v):v is string=>Boolean(v)))]
  const toggleFavorite=(username:string)=>setPreferences(p=>({...p,favorites:p.favorites.includes(username)?p.favorites.filter(v=>v!==username):[...p.favorites,username]}))
  async function enableNotifications(){ if(!('Notification'in window))return; const permission=await Notification.requestPermission(); if(permission==='granted')setPreferences(p=>({...p,notifications:true})) }
  return <div className="app-shell">
    {stats.demo_mode&&<div className="demo-banner">DEMO MODE — simulated local fixtures, never live production data</div>}
    <header><a className="brand" href="#top"><Logo/><div><strong>TikTok-Chests</strong><span>Unofficial LIVE intelligence</span></div></a><nav aria-label="Primary"><a href="#radar"><Radio/>LIVE Radar</a><button onClick={()=>setPreferences(p=>({...p,filters:{...p.filters,favoritesOnly:!p.filters.favoritesOnly}}))}><Heart/>Favorites <i>{preferences.favorites.length}</i></button><a href="#monitor"><Signal/>Monitoring</a></nav><div className="header-actions"><button className="icon-button" onClick={()=>setSettingsOpen(true)} aria-label="Open settings"><Settings size={18}/></button><span className={`connection ${connection}`}><i/>{connection}</span></div></header>
    <main id="top">
      <section className="hero"><div><span className="eyebrow"><ShieldCheck size={14}/> Public streams · manual claims</span><h1>Treasure Box <em>LIVE Radar</em></h1><p>Monitor genuine envelope events from configured public TikTok LIVE streams. No login, no automated claiming, no fabricated production data.</p></div><div className="freshness">{stats.last_update_at?<>Last update<strong>{new Date(stats.last_update_at).toLocaleTimeString()}</strong></>:<>Radar status<strong>{connection}</strong></>}</div></section>
      {error&&<div className="alert" role="alert"><WifiOff/><div><b>Backend connection interrupted</b><p>{error} The radar will reconnect automatically.</p></div></div>}
      <section className="stats-grid" aria-label="Session statistics">
        <div><Radio/><span>Monitored</span><strong>{stats.monitored_streams}</strong><small>{stats.connected_streams} connected</small></div><div><Boxes/><span>Active boxes</span><strong>{stats.active_chests}</strong><small>{stats.detected_total} this session</small></div><div className="gold"><Coins/><span>Known coins</span><strong>{new Intl.NumberFormat().format(totalCoins)}</strong><small>Only reported totals</small></div><div><Signal/><span>Queue</span><strong>{stats.queued_streams}</strong><small>{stats.events_received} events observed</small></div>
      </section>
      <Filters filters={preferences.filters} sort={preferences.sort} regions={regions} rewardTypes={rewards} onFilters={filters=>setPreferences(p=>({...p,filters}))} onSort={sort=>setPreferences(p=>({...p,sort}))}/>
      <section id="radar" className="radar"><div className="section-title"><div><span className="eyebrow">Real-time opportunities</span><h2>Active Treasure Boxes</h2></div><span className="result-count">{visible.length} result{visible.length===1?'':'s'}</span></div>
        {connection!=='connected'&&chests.length===0?<div className="empty"><div className="pulse-radar"><Radio/></div><h3>{connection==='offline'?'Backend unavailable':'Connecting to radar…'}</h3><p>Live state will appear after the WebSocket snapshot arrives.</p></div>:chests.length===0?<div className="empty"><Boxes/><h3>No Treasure Boxes detected</h3><p>The scanner is available, but configured streams have not emitted a supported EnvelopeEvent. Add a public LIVE below.</p><a href="#monitor">Configure monitoring</a></div>:visible.length===0?<div className="empty"><CircleHelp/><h3>No results match your filters</h3><p>Reset filters or include more streamers to widen the radar.</p><button onClick={()=>setPreferences(p=>({...p,filters:defaults.filters}))}>Reset filters</button></div>:<div className="card-grid">{visible.map(chest=><ChestCard key={chest.id} chest={chest} now={now} favorite={preferences.favorites.includes(chest.streamer_username)} onFavorite={()=>toggleFavorite(chest.streamer_username)}/>)}</div>}
      </section>
      <MonitorPanel stats={stats} streams={streams} addStream={addStream} removeStream={removeStream}/>
    </main>
    <footer><div><Logo/><p><b>TikTok-Chests</b> is an open-source, unofficial informational tool and is not affiliated with TikTok or ByteDance.</p></div><p>Rewards must be claimed manually in TikTok. Availability and browser background notifications are not guaranteed.</p></footer>
    {settingsOpen&&<div className="modal-backdrop" onMouseDown={()=>setSettingsOpen(false)}><section className="settings-modal" role="dialog" aria-modal="true" aria-labelledby="settings-title" onMouseDown={e=>e.stopPropagation()}><div className="modal-head"><div><span className="eyebrow">Local preferences</span><h2 id="settings-title">Settings</h2></div><button className="icon-button" onClick={()=>setSettingsOpen(false)} aria-label="Close settings"><X/></button></div>
      <label className="setting-row"><div><b>Browser notifications</b><span>Alerts for new genuine live events.</span></div><input type="checkbox" checked={preferences.notifications} onChange={e=>e.target.checked?void enableNotifications():setPreferences(p=>({...p,notifications:false}))}/></label>
      <label className="setting-row"><div><b>Favorites only for notifications</b><span>Reduce alert noise.</span></div><input type="checkbox" checked={preferences.favoriteNotifications} onChange={e=>setPreferences(p=>({...p,favoriteNotifications:e.target.checked}))}/></label>
      <label className="setting-field"><span>Minimum coin threshold</span><input type="number" min="0" value={preferences.coinThreshold} onChange={e=>setPreferences(p=>({...p,coinThreshold:Number(e.target.value)}))}/></label>
      <div className="notice"><Bell/><p>Notification permission is requested only when you enable it. Background delivery depends on the browser and is not guaranteed.</p></div><button className="danger-button" onClick={reset}>Reset all local settings</button>
    </section></div>}
  </div>
}
export default App
