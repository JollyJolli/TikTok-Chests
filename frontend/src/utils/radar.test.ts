import { describe, expect, it } from 'vitest'
import type { Chest } from '../types'
import { defaultFilters, filterChests, formatCountdown, sortChests } from './radar'

const base: Chest = { id:'1',streamer_username:'alice',streamer_display_name:'Alice',avatar_url:null,room_id:null,live_url:'https://www.tiktok.com/@alice/live',coins:100,winners:10,coins_per_winner:10,opportunity_score:50,reward_type:'coins',opens_at:new Date(200_000).toISOString(),expires_at:null,chest_type:null,region:null,participants:null,viewer_count:20,detected_at:new Date(0).toISOString(),updated_at:new Date(0).toISOString(),status:'upcoming',source:'live' }
describe('radar utilities',()=>{
  it('formats countdowns',()=>{ expect(formatCountdown(65)).toBe('1:05'); expect(formatCountdown(0)).toBe('Open now'); expect(formatCountdown(null)).toBe('Time unavailable') })
  it('filters on supported fields and favorites',()=>{ expect(filterChests([base],{...defaultFilters,minCoins:101},[],0)).toHaveLength(0); expect(filterChests([base],{...defaultFilters,favoritesOnly:true},['alice'],0)).toHaveLength(1) })
  it('sorts missing values last',()=>{ const high={...base,id:'2',coins:500}; expect(sortChests([base,high],'coins')[0].id).toBe('2') })
})
