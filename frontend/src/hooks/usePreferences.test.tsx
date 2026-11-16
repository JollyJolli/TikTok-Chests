import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { usePreferences } from './usePreferences'
describe('usePreferences',()=>{beforeEach(()=>localStorage.clear());it('persists favorites',()=>{const {result}=renderHook(()=>usePreferences());act(()=>result.current.setPreferences(p=>({...p,favorites:['alice']})));expect(JSON.parse(localStorage.getItem('tiktok-chests.preferences.v1')||'{}').favorites).toEqual(['alice'])})})
