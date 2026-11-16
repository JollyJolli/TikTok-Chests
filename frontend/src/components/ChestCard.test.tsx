import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Chest } from '../types'
import { ChestCard } from './ChestCard'

const chest:Chest={id:'1',streamer_username:'alice',streamer_display_name:'Alice',avatar_url:null,room_id:'1',live_url:'https://www.tiktok.com/@alice/live',coins:null,winners:null,coins_per_winner:null,opportunity_score:null,reward_type:null,opens_at:null,expires_at:null,chest_type:null,region:null,participants:null,viewer_count:null,detected_at:new Date().toISOString(),updated_at:new Date().toISOString(),status:'upcoming',source:'live'}
describe('ChestCard',()=>{it('renders missing data honestly and verified link',()=>{render(<ChestCard chest={chest} favorite={false} now={0} onFavorite={vi.fn()}/>);expect(screen.getByText('Alice')).toBeInTheDocument();expect(screen.getByText('Time unavailable')).toBeInTheDocument();expect(screen.getByRole('link',{name:/open live/i})).toHaveAttribute('href',chest.live_url)})})
