'use client'

import { useState, useEffect } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  ColumnDef,
} from '@tanstack/react-table'
import { supabase } from '@/lib/supabase'
import { Button } from './ui/button'
import { Plus, Trash2, Edit2 } from 'lucide-react'

interface DataGridProps {
  tableName: string
  sheetId: string
  tabName: string
}

export function DataGrid({ tableName, sheetId, tabName }: DataGridProps) {
  const [data, setData] = useState<any[]>([])
  const [columns, setColumns] = useState<ColumnDef<any>[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [tableName])

  async function loadData() {
    setLoading(true)
    setError(null)
    
    try {
      const { data: rows, error: fetchError } = await supabase
        .from(tableName)
        .select('*')
        .limit(100)

      if (fetchError) throw fetchError

      if (rows && rows.length > 0) {
        const columnKeys = Object.keys(rows[0]).filter(
          key => !['id', 'created_at', 'updated_at'].includes(key)
        )
        
        const dynamicColumns: ColumnDef<any>[] = columnKeys.map(key => ({
          accessorKey: key,
          header: () => (
            <div className="flex items-center gap-2 font-semibold text-xs uppercase text-gray-500">
              {key.replace(/_/g, ' ')}
            </div>
          ),
          cell: ({ getValue }) => (
            <div className="px-2 py-1 text-sm">
              {getValue() as string || '-'}
            </div>
          ),
        }))

        setColumns([
          {
            id: 'actions',
            header: () => <div className="w-10"></div>,
            cell: ({ row }) => (
              <div className="flex items-center gap-1">
                <button
                  onClick={() => handleDelete(row.original.id)}
                  className="p-1 hover:bg-red-50 rounded text-red-500"
                  title="Delete row"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ),
            size: 40,
          },
          ...dynamicColumns
        ])
        
        setData(rows)
      } else {
        setData([])
        setColumns([])
      }
    } catch (err: any) {
      setError(err.message)
      console.error('Error loading data:', err)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Are you sure you want to delete this row?')) return
    
    try {
      const { error } = await supabase
        .from(tableName)
        .delete()
        .eq('id', id)

      if (error) throw error
      
      await loadData()
    } catch (err: any) {
      alert('Error deleting row: ' + err.message)
    }
  }

  async function handleAddRow() {
    const newRow: any = {}
    columns.forEach(col => {
      if (col.id !== 'actions' && 'accessorKey' in col) {
        newRow[col.accessorKey as string] = ''
      }
    })

    try {
      const { error } = await supabase
        .from(tableName)
        .insert([newRow])

      if (error) throw error
      
      await loadData()
    } catch (err: any) {
      alert('Error adding row: ' + err.message)
    }
  }

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">Error: {error}</div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b bg-white">
        <div>
          <h2 className="text-lg font-semibold">{tableName}</h2>
          <p className="text-xs text-gray-500">{data.length} rows</p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={handleAddRow} size="sm">
            <Plus size={16} />
            Add Row
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 bg-gray-50 border-b">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th
                    key={header.id}
                    className="px-4 py-2 text-left border-r last:border-r-0"
                    style={{ width: header.getSize() }}
                  >
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map(row => (
              <tr
                key={row.id}
                className="border-b hover:bg-gray-50 transition-colors"
              >
                {row.getVisibleCells().map(cell => (
                  <td
                    key={cell.id}
                    className="border-r last:border-r-0"
                  >
                    {flexRender(
                      cell.column.columnDef.cell,
                      cell.getContext()
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
