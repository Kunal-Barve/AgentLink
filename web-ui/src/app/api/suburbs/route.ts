import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'http://srv1165267.hstgr.cloud:8000'
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: { persistSession: false },
})

/**
 * GET /api/suburbs
 * 
 * Query params:
 *   action=states         → returns distinct state codes
 *   action=suburbs&state=NSW&search=dar  → returns suburbs for a state (with optional search)
 *   action=postcodes&state=NSW&suburb=DARWIN CITY → returns postcodes for a suburb+state combo
 */
export async function GET(request: NextRequest) {
  const action = request.nextUrl.searchParams.get('action')
  const state = request.nextUrl.searchParams.get('state')
  const suburb = request.nextUrl.searchParams.get('suburb')
  const search = request.nextUrl.searchParams.get('search')

  try {
    if (action === 'states') {
      // Get distinct state codes, sorted
      const { data, error } = await supabase
        .from('au_suburbs')
        .select('state')
        .order('state')

      if (error) throw error

      const states = [...new Set((data || []).map((r: any) => r.state))].sort()
      return NextResponse.json({ states })
    }

    if (action === 'suburbs') {
      if (!state) {
        return NextResponse.json({ error: 'state parameter is required' }, { status: 400 })
      }

      let query = supabase
        .from('au_suburbs')
        .select('suburb')
        .eq('state', state.toUpperCase())
        .order('suburb')

      if (search && search.trim()) {
        query = query.ilike('suburb', `%${search.trim()}%`)
      }

      // Limit results to prevent massive payloads
      query = query.limit(100)

      const { data, error } = await query

      if (error) throw error

      // Deduplicate suburb names (a suburb can have multiple postcodes)
      const suburbs = [...new Set((data || []).map((r: any) => r.suburb))].sort()
      return NextResponse.json({ suburbs })
    }

    if (action === 'postcodes') {
      if (!state || !suburb) {
        return NextResponse.json({ error: 'state and suburb parameters are required' }, { status: 400 })
      }

      const { data, error } = await supabase
        .from('au_suburbs')
        .select('postcode')
        .eq('state', state.toUpperCase())
        .ilike('suburb', suburb.trim())
        .order('postcode')

      if (error) throw error

      const postcodes = [...new Set((data || []).map((r: any) => r.postcode))].sort()
      return NextResponse.json({ postcodes })
    }

    return NextResponse.json({ error: 'Invalid action. Use states, suburbs, or postcodes.' }, { status: 400 })
  } catch (err: any) {
    console.error('Error in suburbs API:', err)
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
