import { NextRequest, NextResponse } from 'next/server'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'http://srv1165267.hstgr.cloud:8000'
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

export async function GET(request: NextRequest) {
  const tableName = request.nextUrl.searchParams.get('table')

  if (!tableName) {
    return NextResponse.json({ error: 'table parameter is required' }, { status: 400 })
  }

  try {
    // Fetch the OpenAPI spec from Supabase REST API
    const res = await fetch(`${supabaseUrl}/rest/v1/`, {
      headers: {
        'apikey': supabaseKey,  
        'Authorization': `Bearer ${supabaseKey}`,
      },
    })

    if (!res.ok) {
      throw new Error(`Supabase REST API returned ${res.status}`)
    }

    const spec = await res.json()

    // Look for the table definition in the OpenAPI spec
    let columns: string[] = []

    if (spec.definitions && spec.definitions[tableName]) {
      const def = spec.definitions[tableName]
      if (def.properties) {
        columns = Object.keys(def.properties).filter(
          col => !['id', 'created_at', 'updated_at'].includes(col)
        )
      }
    }

    return NextResponse.json({ columns })
  } catch (err: any) {
    console.error('Error fetching columns:', err)
    return NextResponse.json({ error: err.message }, { status: 500 })
  }
}
