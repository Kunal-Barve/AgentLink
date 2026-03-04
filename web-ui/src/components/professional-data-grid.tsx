'use client'

import { useState, useEffect, useRef } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  ColumnDef,
  getSortedRowModel,
  SortingState,
  getFilteredRowModel,
  ColumnResizeMode,
  ColumnFiltersState,
} from '@tanstack/react-table'
import { supabase } from '@/lib/supabase'
import { ChevronDown, ChevronUp, Plus, Trash2, Search, X, Download, Palette } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DataGridProps {
  tableName: string
  sheetId: string
  tabName: string
}

export function ProfessionalDataGrid({ tableName, sheetId, tabName }: DataGridProps) {
  const [data, setData] = useState<any[]>([])
  const [columns, setColumns] = useState<ColumnDef<any>[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [globalFilter, setGlobalFilter] = useState('')
  const [columnResizeMode] = useState<ColumnResizeMode>('onChange')
  const [editingCell, setEditingCell] = useState<{ rowIndex: number; columnId: string } | null>(null)
  const [editValue, setEditValue] = useState('')
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set())
  const [rowColors, setRowColors] = useState<Map<number, string>>(new Map())

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
        .order('id', { ascending: true })

      if (fetchError) throw fetchError

      if (rows && rows.length > 0) {
        const columnKeys = Object.keys(rows[0]).filter(
          key => !['created_at', 'updated_at'].includes(key)
        )
        
        const dynamicColumns: ColumnDef<any>[] = columnKeys.map(key => ({
          accessorKey: key,
          id: key,
          size: key === 'id' ? 80 : 200,
          minSize: 60,
          maxSize: 600,
          enableResizing: true,
          header: ({ column }) => (
            <div 
              className="flex items-center justify-between h-full px-3 cursor-pointer select-none group"
              onClick={() => column.toggleSorting()}
            >
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide truncate">
                {key.replace(/_/g, ' ')}
              </span>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {column.getIsSorted() === 'asc' && <ChevronUp size={14} />}
                {column.getIsSorted() === 'desc' && <ChevronDown size={14} />}
              </div>
            </div>
          ),
          cell: ({ row, column }) => {
            const cellId = `${row.original.id}-${column.id}`
            const isEditing = editingCell?.rowIndex === row.index && editingCell?.columnId === column.id
            const value = row.getValue(column.id) as string
            
            return (
              <div
                className={cn(
                  "h-full px-3 py-2 text-sm flex items-center",
                  key === 'id' ? 'text-muted-foreground font-mono' : 'text-foreground',
                  isEditing && 'p-0'
                )}
                onClick={() => {
                  if (key !== 'id') {
                    setEditingCell({ rowIndex: row.index, columnId: column.id as string })
                    setEditValue(value || '')
                  }
                }}
              >
                {isEditing ? (
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onBlur={() => handleCellUpdate(row.original.id, column.id as string, editValue)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleCellUpdate(row.original.id, column.id as string, editValue)
                      } else if (e.key === 'Escape') {
                        setEditingCell(null)
                      }
                    }}
                    autoFocus
                    className="w-full h-full px-3 py-2 bg-background border-2 border-primary focus:outline-none text-sm"
                  />
                ) : (
                  <span className={cn("truncate", !value && "text-muted-foreground")}>
                    {value || '-'}
                  </span>
                )}
              </div>
            )
          },
        }))
        
        setColumns(dynamicColumns)
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

  async function handleCellUpdate(rowId: number, columnId: string, value: string) {
    try {
      const { error } = await supabase
        .from(tableName)
        .update({ [columnId]: value })
        .eq('id', rowId)

      if (error) throw error
      
      setData(prev => prev.map(row => 
        row.id === rowId ? { ...row, [columnId]: value } : row
      ))
    } catch (err: any) {
      console.error('Update failed:', err)
    } finally {
      setEditingCell(null)
    }
  }

  async function handleDeleteRow(id: number) {
    if (!confirm('Delete this row?')) return
    
    try {
      const { error } = await supabase
        .from(tableName)
        .delete()
        .eq('id', id)

      if (error) throw error
      
      await loadData()
    } catch (err: any) {
      alert('Error: ' + err.message)
    }
  }

  async function handleAddRow() {
    const newRow: any = {}
    columns.forEach(col => {
      if ('accessorKey' in col && col.accessorKey !== 'id') {
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
      alert('Error: ' + err.message)
    }
  }

  const table = useReactTable({
    data,
    columns,
    columnResizeMode,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    state: {
      sorting,
    },
    enableColumnResizing: true,
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-destructive">Error: {error}</div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-card">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold">{tableName.replace(/_/g, ' ')}</h2>
          <span className="text-xs text-muted-foreground">{data.length} records</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleAddRow}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <Plus size={16} />
            Add Record
          </button>
        </div>
      </div>

      {/* Data Grid */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse">
          <thead className="sticky top-0 z-10 bg-card border-b border-border">
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header, idx) => (
                  <th
                    key={header.id}
                    className="relative border-r border-border last:border-r-0 h-10"
                    style={{ width: header.getSize() }}
                  >
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                    {/* Resize handle */}
                    {idx < headerGroup.headers.length - 1 && (
                      <div
                        onMouseDown={header.getResizeHandler()}
                        onTouchStart={header.getResizeHandler()}
                        className={cn(
                          "absolute right-0 top-0 h-full w-1 cursor-col-resize select-none touch-none hover:bg-primary transition-colors",
                          header.column.getIsResizing() && 'bg-primary'
                        )}
                      />
                    )}
                  </th>
                ))}
                <th className="w-12 border-r-0 bg-card"></th>
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row, rowIdx) => (
              <tr
                key={row.id}
                className="group border-b border-border hover:bg-accent/50 transition-colors"
              >
                {row.getVisibleCells().map(cell => (
                  <td
                    key={cell.id}
                    className="border-r border-border last:border-r-0 h-10"
                    style={{ width: cell.column.getSize() }}
                  >
                    {flexRender(
                      cell.column.columnDef.cell,
                      cell.getContext()
                    )}
                  </td>
                ))}
                <td className="w-12 text-center">
                  <button
                    onClick={() => handleDeleteRow(row.original.id)}
                    className="p-1 opacity-0 group-hover:opacity-100 hover:bg-destructive/10 rounded transition-all"
                    title="Delete row"
                  >
                    <Trash2 size={14} className="text-destructive" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
