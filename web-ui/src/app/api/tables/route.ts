import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'http://srv1165267.hstgr.cloud:8000'
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

// System/internal tables to exclude from the UI
const EXCLUDED_TABLES = new Set([
  'au_suburbs',         // lookup table, not a sheet
  'schema_migrations',
  'spatial_ref_sys',
])

interface SheetGroup {
  id: string
  name: string
  tabs: { name: string; tableName: string; displayName: string }[]
}

// Known short words that should be uppercased (state codes, acronyms)
const UPPERCASE_WORDS = new Set([
  'nsw', 'vic', 'qld', 'sa', 'wa', 'nt', 'act', 'tas',
  'id', 'api', 'url', 'csv', 'pdf', 'mrr',
])

/**
 * Title-case a word, but uppercase known acronyms/state codes.
 */
function titleWord(w: string): string {
  if (UPPERCASE_WORDS.has(w.toLowerCase())) return w.toUpperCase()
  return w.charAt(0).toUpperCase() + w.slice(1)
}

/**
 * Find the longest common prefix (at underscore boundaries) between two table names.
 */
function commonPrefix(a: string, b: string): string {
  const partsA = a.split('_')
  const partsB = b.split('_')
  const shared: string[] = []
  for (let i = 0; i < Math.min(partsA.length, partsB.length); i++) {
    if (partsA[i] === partsB[i]) shared.push(partsA[i])
    else break
  }
  return shared.join('_')
}

/**
 * Given a list of Supabase table names, group them into "sheets" with "tabs".
 *
 * Naming convention (from Google Sheets → Supabase):
 *   base_table           → Sheet "Base Table",   Tab "Sheet1" (default)
 *   base_table_tab_name  → Sheet "Base Table",   Tab "Tab Name"
 *
 * Algorithm:
 *   1. Sort table names alphabetically (shortest/base comes first).
 *   2. Greedy grouping: for each table, check if it starts with
 *      any existing group's base prefix + "_". If yes → add as tab.
 *      If no → start a new group.
 *   3. Second pass: for remaining single-table groups, find pairs that
 *      share a specific common prefix (≥3 underscore-separated parts)
 *      and merge them.
 */
function groupTables(tableNames: string[]): SheetGroup[] {
  const sorted = [...tableNames].sort()

  // Pass 1: greedy grouping — sorted ensures the base table (shorter) comes first
  const groups: { base: string; tables: string[] }[] = []

  for (const table of sorted) {
    let matched = false
    // Check against existing groups
    for (const group of groups) {
      if (table.startsWith(group.base + '_')) {
        group.tables.push(table)
        matched = true
        break
      }
    }
    if (!matched) {
      groups.push({ base: table, tables: [table] })
    }
  }

  // Pass 2: merge single-table groups that share a long common prefix
  const singles = groups.filter(g => g.tables.length === 1)
  const multis = groups.filter(g => g.tables.length > 1)
  const usedSingles = new Set<string>()
  const merged: { base: string; tables: string[] }[] = []

  // Build a map of all possible prefixes (≥3 parts) → list of singles
  const prefixMap = new Map<string, string[]>()
  for (const s of singles) {
    const parts = s.base.split('_')
    // Try prefixes from longest to 3 parts minimum
    for (let len = parts.length - 1; len >= 3; len--) {
      const prefix = parts.slice(0, len).join('_')
      if (!prefixMap.has(prefix)) prefixMap.set(prefix, [])
      prefixMap.get(prefix)!.push(s.base)
    }
  }

  // Find the longest prefix that groups 2+ unused singles
  // Sort prefixes by length descending to prefer longer (more specific) matches
  const sortedPrefixes = [...prefixMap.entries()]
    .filter(([, tables]) => tables.length >= 2)
    .sort((a, b) => b[0].length - a[0].length)

  for (const [prefix, tables] of sortedPrefixes) {
    const unused = tables.filter(t => !usedSingles.has(t))
    if (unused.length >= 2) {
      merged.push({ base: prefix, tables: unused })
      unused.forEach(t => usedSingles.add(t))
    }
  }

  // Combine: multis + merged + remaining singles
  const result: { base: string; tables: string[] }[] = [...multis, ...merged]
  for (const s of singles) {
    if (!usedSingles.has(s.base)) {
      result.push(s)
    }
  }

  // Convert to SheetGroup format
  return result.map(group => {
    const id = group.base.replace(/_/g, '-')
    const name = group.base.split('_').map(titleWord).join(' ')

    const tabs = group.tables.sort().map(table => {
      if (table === group.base) {
        return { name: 'sheet1', tableName: table, displayName: 'Sheet1' }
      }
      const suffix = table.slice(group.base.length + 1)
      const tabDisplayName = suffix.split('_').map(titleWord).join(' ')
      return {
        name: suffix.replace(/_/g, '-'),
        tableName: table,
        displayName: tabDisplayName,
      }
    })

    return { id, name, tabs }
  }).sort((a, b) => a.name.localeCompare(b.name))
}

export async function GET() {
  try {
    // Method: Query the Supabase REST API's OpenAPI spec to get table names
    // The root endpoint returns an OpenAPI spec with all available tables
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

    // The OpenAPI spec has paths like "/table_name" for each table
    let tableNames: string[] = []

    if (spec.paths) {
      tableNames = Object.keys(spec.paths)
        .map(path => path.replace(/^\//, ''))  // remove leading slash
        .filter(name => name && !name.includes('/'))  // only top-level paths
        .filter(name => !EXCLUDED_TABLES.has(name))
        .filter(name => !name.startsWith('_'))  // exclude internal tables
    } else if (spec.definitions) {
      // Fallback: use definitions from OpenAPI spec
      tableNames = Object.keys(spec.definitions)
        .filter(name => !EXCLUDED_TABLES.has(name))
        .filter(name => !name.startsWith('_'))
    }

    if (tableNames.length === 0) {
      return NextResponse.json({ sheets: [], tableNames: [] })
    }

    const sheets = groupTables(tableNames)

    return NextResponse.json({ sheets, tableNames })
  } catch (err: any) {
    console.error('Error fetching tables:', err)
    return NextResponse.json(
      { error: err.message || 'Failed to fetch tables' },
      { status: 500 }
    )
  }
}
