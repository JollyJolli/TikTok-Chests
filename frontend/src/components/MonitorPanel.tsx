import { Activity, Plus, Radio, Trash2 } from 'lucide-react'
import { FormEvent, useState } from 'react'
import type { Stats, StreamState } from '../types'

interface Props { stats: Stats; streams: StreamState[]; addStream: (value:string)=>Promise<unknown>; removeStream:(value:string)=>Promise<void> }
export function MonitorPanel({stats,streams,addStream,removeStream}:Props) { const [value,setValue]=useState(''); const [message,setMessage]=useState(''); const [busy,setBusy]=useState(false)
  async function submit(e:FormEvent){e.preventDefault();setBusy(true);setMessage('');try{await addStream(value);setMessage('Added to the monitoring queue.');setValue('')}catch(error){setMessage(error instanceof Error?error.message:'Could not add stream')}finally{setBusy(false)}}
  return <section className="monitor-panel" id="monitor"><div className="section-title"><div><span className="eyebrow">Scanner operations</span><h2>Monitoring</h2></div><span className="mode"><Radio size={14}/>{stats.discovery_mode} mode</span></div>
    <div className="limitations"><Activity size={18}/><div><b>{stats.discovery_available?'Automatic discovery active':'Manual monitoring fallback'}</b><p>{stats.discovery_message}</p></div></div>
    <form onSubmit={submit} className="monitor-form"><label htmlFor="stream">Public username or LIVE URL</label><div><input id="stream" required value={value} onChange={e=>setValue(e.target.value)} placeholder="@creator or https://www.tiktok.com/@creator/live"/><button disabled={busy}><Plus size={16}/>{busy?'Adding…':'Monitor'}</button></div>{message&&<p role="status">{message}</p>}</form>
    <div className="stream-list">{streams.length===0?<p className="muted">No livestreams are configured yet.</p>:streams.map(stream=><div key={stream.username}><span className={`status-dot ${stream.status}`}/><div><b>@{stream.username}</b><small>{stream.last_error||stream.status}</small></div><button onClick={()=>void removeStream(stream.username)} aria-label={`Stop monitoring ${stream.username}`}><Trash2 size={16}/></button></div>)}</div>
  </section>
}
