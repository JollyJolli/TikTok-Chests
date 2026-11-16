import { RotateCcw, Search, SlidersHorizontal } from 'lucide-react'
import type { Filters as FilterType, SortKey } from '../types'

interface Props { filters: FilterType; sort: SortKey; regions: string[]; rewardTypes: string[]; onFilters: (value: FilterType) => void; onSort: (value: SortKey) => void }
export function Filters({ filters, sort, regions, rewardTypes, onFilters, onSort }: Props) {
  const update = (name: keyof FilterType, value: string|number|boolean) => onFilters({ ...filters, [name]: value })
  return <section className="filter-panel" aria-label="Radar filters"><div className="filter-heading"><span><SlidersHorizontal size={17}/> Filters</span><button onClick={() => onFilters({search:'',minCoins:0,maxViewers:0,minWinners:0,minCoinsPerWinner:0,maxMinutes:0,rewardType:'',region:'',favoritesOnly:false})}><RotateCcw size={14}/> Reset</button></div>
    <div className="search"><Search size={17}/><input value={filters.search} onChange={(e)=>update('search',e.target.value)} placeholder="Search streamer" aria-label="Search streamer"/></div>
    <div className="filter-grid">
      <label>Sort<select value={sort} onChange={(e)=>onSort(e.target.value as SortKey)}><option value="recommended">Recommended</option><option value="coins">Highest coins</option><option value="cpw">Coins per winner</option><option value="viewers">Lowest viewers</option><option value="winners">Most winners</option><option value="opening">Opening soonest</option><option value="recent">Recently detected</option></select></label>
      <label>Minimum coins<input type="number" min="0" value={filters.minCoins||''} onChange={(e)=>update('minCoins',Number(e.target.value))}/></label>
      <label>Maximum viewers<input type="number" min="0" value={filters.maxViewers||''} onChange={(e)=>update('maxViewers',Number(e.target.value))}/></label>
      <label>Minimum winners<input type="number" min="0" value={filters.minWinners||''} onChange={(e)=>update('minWinners',Number(e.target.value))}/></label>
      <label>Coins per winner<input type="number" min="0" value={filters.minCoinsPerWinner||''} onChange={(e)=>update('minCoinsPerWinner',Number(e.target.value))}/></label>
      <label>Opens within<select value={filters.maxMinutes} onChange={(e)=>update('maxMinutes',Number(e.target.value))}><option value="0">Any time</option><option value="1">1 minute</option><option value="5">5 minutes</option><option value="10">10 minutes</option></select></label>
      {rewardTypes.length>1 && <label>Reward type<select value={filters.rewardType} onChange={(e)=>update('rewardType',e.target.value)}><option value="">All</option>{rewardTypes.map(v=><option key={v}>{v}</option>)}</select></label>}
      {regions.length>0 && <label>Verified region<select value={filters.region} onChange={(e)=>update('region',e.target.value)}><option value="">All</option>{regions.map(v=><option key={v}>{v}</option>)}</select></label>}
    </div><label className="check"><input type="checkbox" checked={filters.favoritesOnly} onChange={(e)=>update('favoritesOnly',e.target.checked)}/> Favorites only</label>
  </section>
}
