import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'http://srv1165267.hstgr.cloud:8000'
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

const supabaseAdmin = createClient(supabaseUrl, supabaseServiceKey, {
  auth: { persistSession: false }
})

export async function POST(request: NextRequest) {
  try {
    const { tableName, columns } = await request.json()

    if (!tableName || !columns || columns.length === 0) {
      return NextResponse.json(
        { error: 'Table name and at least one column are required' },
        { status: 400 }
      )
    }

    // Sanitize table name: lowercase, replace spaces with underscores, remove special chars
    const sanitizedName = tableName
      .toLowerCase()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_]/g, '')

    if (!sanitizedName) {
      return NextResponse.json(
        { error: 'Invalid table name' },
        { status: 400 }
      )
    }

    // Build column definitions
    const columnDefs = columns.map((col: { name: string; type: string }) => {
      const colName = col.name
        .toLowerCase()
        .replace(/\s+/g, '_')
        .replace(/[^a-z0-9_]/g, '')
      
      const pgType = col.type === 'number' ? 'numeric'
        : col.type === 'boolean' ? 'boolean'
        : col.type === 'date' ? 'timestamptz'
        : 'text'

      return `"${colName}" ${pgType}`
    })

    const sql = `
      CREATE TABLE IF NOT EXISTS "${sanitizedName}" (
        id bigint generated always as identity primary key,
        ${columnDefs.join(',\n        ')},
        created_at timestamptz default now(),
        updated_at timestamptz default now()
      );
    `

    const { error } = await supabaseAdmin.rpc('exec_sql', { sql_query: sql })

    if (error) {
      // If the rpc function doesn't exist, try a direct approach
      console.error('RPC exec_sql failed:', error)
      return NextResponse.json(
        { error: `Failed to create table: ${error.message}. You may need to create the table directly in Supabase.` },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      tableName: sanitizedName,
      message: `Table "${sanitizedName}" created successfully`
    })
  } catch (err: any) {
    console.error('Create table error:', err)
    return NextResponse.json(
      { error: err.message || 'Internal server error' },
      { status: 500 }
    )
  }
}
