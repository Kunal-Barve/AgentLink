'use client'

import { useState, useEffect } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  ColumnDef,
  getSortedRowModel,
  SortingState,
  getFilteredRowModel,
  ColumnFiltersState,
  FilterFn,
} from '@tanstack/react-table'
import { supabase } from '@/lib/supabase'
import { ChevronDown, ChevronUp, Plus, Trash2, Search, X, Download, Palette, Check, Filter } from 'lucide-react'
import { cn } from '@/lib/utils'

const globalFilterFn: FilterFn<any> = (row, columnId, filterValue) => {
  const search = String(filterValue).toLowerCase()
  const values = Object.values(row.original)
  return values.some(val => String(val ?? '').toLowerCase().includes(search))
}

const columnFilterFn: FilterFn<any> = (row, columnId, filterValue) => {
  const cellValue = String(row.getValue(columnId) ?? '').toLowerCase()
  return cellValue.includes(String(filterValue).toLowerCase())
}

interface DataGridProps {
  tableName: string
  sheetId: string
  tabName: string
}

const COLORS = [
  { name: 'None', value: '', class: '' },
  { name: 'Red', value: 'red', class: 'bg-red-500/10 hover:bg-red-500/20' },
  { name: 'Orange', value: 'orange', class: 'bg-orange-500/10 hover:bg-orange-500/20' },
  { name: 'Yellow', value: 'yellow', class: 'bg-yellow-500/10 hover:bg-yellow-500/20' },
  { name: 'Green', value: 'green', class: 'bg-green-500/10 hover:bg-green-500/20' },
  { name: 'Blue', value: 'blue', class: 'bg-blue-500/10 hover:bg-blue-500/20' },
  { name: 'Purple', value: 'purple', class: 'bg-purple-500/10 hover:bg-purple-500/20' },
  { name: 'Pink', value: 'pink', class: 'bg-pink-500/10 hover:bg-pink-500/20' },
]

export function BeautifulDataGrid({ tableName, sheetId, tabName }: DataGridProps) {
  const [data, setData] = useState<any[]>([])
  const [columns, setColumns] = useState<ColumnDef<any>[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [globalFilter, setGlobalFilter] = useState('')
  const [editingCell, setEditingCell] = useState<{ rowIndex: number; columnId: string } | null>(null)
  const [editValue, setEditValue] = useState('')
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set())
  const [rowColors, setRowColors] = useState<Map<number, string>>(new Map())
  const [showColorPicker, setShowColorPicker] = useState<number | null>(null)
  const [showColumnFilter, setShowColumnFilter] = useState<string | null>(null)
  const [hoveredColumn, setHoveredColumn] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [tableName])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        if (e.key === 'a') {
          e.preventDefault()
          const allIndices = new Set(data.map((_, idx) => idx))
          setSelectedRows(allIndices)
        } else if (e.key === 'e') {
          e.preventDefault()
          exportToCSV()
        }
      }
      if (e.key === 'Escape') {
        setSelectedRows(new Set())
        setEditingCell(null)
      }
      if (e.key === 'Delete' && selectedRows.size > 0) {
        handleBulkDelete()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [data, selectedRows])

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
          key => !['id', 'created_at', 'updated_at'].includes(key)
        )
        
        const dynamicColumns: ColumnDef<any>[] = columnKeys.map(key => ({
          accessorKey: key,
          id: key,
          size: 200,
          minSize: 100,
          maxSize: 600,
          enableResizing: true,
          filterFn: columnFilterFn,
          header: ({ column }) => (
            <div 
              className="flex items-center justify-between h-full px-3 group"
              onMouseEnter={() => setHoveredColumn(key)}
              onMouseLeave={() => setHoveredColumn(null)}
            >
              <button
                onClick={() => column.toggleSorting()}
                className="flex items-center gap-2 flex-1 text-left"
              >
                <span className="text-xs font-semibold text-foreground uppercase tracking-wide truncate">
                  {key.replace(/_/g, ' ')}
                </span>
                {column.getIsSorted() === 'asc' && <ChevronUp size={14} className="text-primary" />}
                {column.getIsSorted() === 'desc' && <ChevronDown size={14} className="text-primary" />}
              </button>
              <button
                onClick={() => setShowColumnFilter(showColumnFilter === key ? null : key)}
                className="p-1 hover:bg-primary/20 rounded transition-colors"
              >
                <Filter size={14} className={cn(
                  "transition-colors",
                  columnFilters.some(f => f.id === key) ? "text-primary" : "text-muted-foreground"
                )} />
              </button>
            </div>
          ),
          cell: ({ row, column }) => {
            const rowIndex = row.index
            const isEditing = editingCell?.rowIndex === rowIndex && editingCell?.columnId === column.id
            const value = row.getValue(column.id) as string
            const isHovered = hoveredColumn === column.id
            
            return (
              <div
                className={cn(
                  "h-full px-3 py-2.5 text-sm flex items-center cursor-text transition-all",
                  isHovered && "bg-primary/5",
                  isEditing && "p-0"
                )}
                onClick={() => {
                  setEditingCell({ rowIndex, columnId: column.id as string })
                  setEditValue(value || '')
                }}
              >
                {isEditing ? (
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onBlur={() => handleCellUpdate(rowIndex, column.id as string, editValue)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleCellUpdate(rowIndex, column.id as string, editValue)
                      } else if (e.key === 'Escape') {
                        setEditingCell(null)
                      }
                    }}
                    autoFocus
                    className="w-full h-full px-3 py-2 bg-background border-2 border-primary focus:outline-none text-sm rounded shadow-lg"
                  />
                ) : (
                  <span className={cn("truncate", !value && "text-muted-foreground italic")}>
                    {value || 'Empty'}
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

  async function handleCellUpdate(rowIndex: number, columnId: string, value: string) {
    try {
      const row = data[rowIndex]
      const { error } = await supabase
        .from(tableName)
        .update({ [columnId]: value })
        .eq('id', row.id)

      if (error) throw error
      
      setData(prev => prev.map((r, idx) => 
        idx === rowIndex ? { ...r, [columnId]: value } : r
      ))
    } catch (err: any) {
      console.error('Update failed:', err)
      alert('Failed to update: ' + err.message)
    } finally {
      setEditingCell(null)
    }
  }

  async function handleDeleteRow(rowIndex: number) {
    if (!confirm('Delete this row?')) return
    
    try {
      const row = data[rowIndex]
      const { error } = await supabase
        .from(tableName)
        .delete()
        .eq('id', row.id)

      if (error) throw error
      
      await loadData()
    } catch (err: any) {
      alert('Error: ' + err.message)
    }
  }

  async function handleBulkDelete() {
    if (!confirm(`Delete ${selectedRows.size} rows?`)) return
    
    try {
      const idsToDelete = Array.from(selectedRows).map(idx => data[idx].id)
      
      for (const id of idsToDelete) {
        await supabase.from(tableName).delete().eq('id', id)
      }
      
      setSelectedRows(new Set())
      await loadData()
    } catch (err: any) {
      alert('Error: ' + err.message)
    }
  }

  async function handleAddRow() {
    const newRow: any = {}
    columns.forEach(col => {
      if ('accessorKey' in col) {
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

  function exportToCSV() {
    const headers = columns.map(col => 'accessorKey' in col ? col.accessorKey : '').filter(Boolean).join(',')
    const rows = data.map(row => 
      columns.map(col => {
        if ('accessorKey' in col) {
          const val = row[col.accessorKey as string] || ''
          return `"${val.toString().replace(/"/g, '""')}"`
        }
        return ''
      }).join(',')
    )
    const csv = [headers, ...rows].join('\n')
    
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${tableName}_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  function toggleRowSelection(rowIndex: number) {
    const newSelected = new Set(selectedRows)
    if (newSelected.has(rowIndex)) {
      newSelected.delete(rowIndex)
    } else {
      newSelected.add(rowIndex)
    }
    setSelectedRows(newSelected)
  }

  function setRowColor(rowIndex: number, color: string) {
    const newColors = new Map(rowColors)
    if (color) {
      newColors.set(rowIndex, color)
    } else {
      newColors.delete(rowIndex)
    }
    setRowColors(newColors)
    setShowColorPicker(null)
  }

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    enableColumnResizing: true,
    globalFilterFn,
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gradient-to-br from-background to-card">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent mb-3"></div>
          <p className="text-muted-foreground">Loading data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center p-6 bg-destructive/10 border border-destructive/20 rounded-lg">
          <p className="text-destructive font-medium">Error loading data</p>
          <p className="text-sm text-muted-foreground mt-1">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full min-h-0 bg-gradient-to-br from-background via-background to-card/50">
      {/* Toolbar with gradient */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between px-4 py-3 border-b border-border bg-gradient-to-r from-card via-card to-card/80 backdrop-blur-sm gap-3 sm:gap-4">
        <div className="flex items-center gap-3">
          <div className="h-8 w-1 bg-gradient-to-b from-primary to-blue-500 rounded-full"></div>
          <div>
            <h2 className="text-sm font-bold bg-gradient-to-r from-foreground to-foreground/60 bg-clip-text text-transparent">
              {tableName.replace(/_/g, ' ')}
            </h2>
            <p className="text-xs text-muted-foreground">
              {data.length} records
              {selectedRows.size > 0 && <span className="text-primary ml-2">• {selectedRows.size} selected</span>}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 flex-wrap w-full sm:w-auto">
          {/* Global Search */}
          <div className="relative flex-1 sm:flex-none">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search all columns..."
              value={globalFilter}
              onChange={(e) => setGlobalFilter(e.target.value)}
              className="pl-9 pr-8 py-2 text-sm bg-background/50 border border-border rounded-lg focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 w-full sm:w-64 transition-all"
            />
            {globalFilter && (
              <button
                onClick={() => setGlobalFilter('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {selectedRows.size > 0 && (
            <button
              onClick={handleBulkDelete}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium bg-gradient-to-r from-destructive/20 to-destructive/10 text-destructive rounded-lg hover:from-destructive/30 hover:to-destructive/20 transition-all border border-destructive/20"
            >
              <Trash2 size={16} />
              Delete ({selectedRows.size})
            </button>
          )}
          
          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium bg-gradient-to-r from-accent to-accent/80 text-foreground rounded-lg hover:from-accent/90 hover:to-accent/70 transition-all shadow-sm"
          >
            <Download size={16} />
            <span className="hidden sm:inline">Export</span>
          </button>
          
          <button
            onClick={handleAddRow}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-gradient-to-r from-primary to-blue-600 text-white rounded-lg hover:from-primary/90 hover:to-blue-600/90 transition-all shadow-lg shadow-primary/20"
          >
            <Plus size={16} />
            <span className="hidden sm:inline">Add Record</span>
          </button>
        </div>
      </div>

      {/* Data Grid with Horizontal + Vertical Scroll */}
      <div className="flex-1 min-h-0 overflow-auto">
        <div style={{ width: 'max-content', minWidth: '100%' }}>
          <table className="w-full border-collapse">
            <thead className="sticky top-0 z-10 bg-gradient-to-b from-card to-card/95 backdrop-blur-sm border-b-2 border-primary/20">
              <tr>
                {/* Checkbox Column */}
                <th className="w-12 border-r border-border/50 bg-card/80">
                  <div className="flex items-center justify-center h-10">
                    <input
                      type="checkbox"
                      checked={selectedRows.size === data.length && data.length > 0}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedRows(new Set(data.map((_, idx) => idx)))
                        } else {
                          setSelectedRows(new Set())
                        }
                      }}
                      className="cursor-pointer w-4 h-4 accent-primary"
                    />
                  </div>
                </th>
                
                {/* Row Number Column */}
                <th className="w-20 border-r border-border/50 bg-card/80 px-3 py-3">
                  <span className="text-xs font-bold text-primary uppercase tracking-wider">#</span>
                </th>

                {/* Data Columns */}
                {table.getHeaderGroups().map(headerGroup => (
                  headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className={cn(
                        "relative border-r border-border/50 last:border-r-0 bg-card/80 transition-colors",
                        hoveredColumn === header.id && "bg-primary/10"
                      )}
                      style={{ minWidth: header.column.columnDef.minSize, width: header.getSize() }}
                    >
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      
                      {/* Column Filter Dropdown */}
                      {showColumnFilter === header.id && (
                        <div className="absolute top-full left-0 mt-1 bg-card border border-primary/30 rounded-lg shadow-2xl p-3 z-20 w-56">
                          <div className="relative">
                            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
                            <input
                              type="text"
                              placeholder={`Filter ${header.id.replace(/_/g, ' ')}...`}
                              value={(columnFilters.find(f => f.id === header.id)?.value as string) || ''}
                              onChange={(e) => {
                                const value = e.target.value
                                setColumnFilters(prev => 
                                  value
                                    ? [...prev.filter(f => f.id !== header.id), { id: header.id, value }]
                                    : prev.filter(f => f.id !== header.id)
                                )
                              }}
                              autoFocus
                              className="w-full pl-8 pr-8 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
                            />
                            {columnFilters.some(f => f.id === header.id) && (
                              <button
                                onClick={() => setColumnFilters(prev => prev.filter(f => f.id !== header.id))}
                                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                              >
                                <X size={14} />
                              </button>
                            )}
                          </div>
                          {columnFilters.some(f => f.id === header.id) && (
                            <button
                              onClick={() => {
                                setColumnFilters(prev => prev.filter(f => f.id !== header.id))
                                setShowColumnFilter(null)
                              }}
                              className="mt-2 w-full text-xs text-center py-1.5 text-destructive hover:bg-destructive/10 rounded-md transition-colors"
                            >
                              Clear filter
                            </button>
                          )}
                        </div>
                      )}
                      
                      {/* Resize Handle */}
                      <div
                        onMouseDown={header.getResizeHandler()}
                        onTouchStart={header.getResizeHandler()}
                        className={cn(
                          "absolute right-0 top-0 h-full w-1 cursor-col-resize select-none touch-none bg-primary/0 hover:bg-primary/50 transition-colors",
                          header.column.getIsResizing() && 'bg-primary'
                        )}
                      />
                    </th>
                  ))
                ))}

                {/* Actions Column */}
                <th className="w-24 bg-card/80 border-l border-border/50 sticky right-0">
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Actions</span>
                </th>
              </tr>
            </thead>
            
            <tbody>
              {table.getRowModel().rows.map((row, rowIdx) => {
                const colorClass = COLORS.find(c => c.value === rowColors.get(rowIdx))?.class || ''
                
                return (
                  <tr
                    key={row.id}
                    className={cn(
                      "group border-b border-border/30 transition-all duration-150",
                      "hover:bg-gradient-to-r hover:from-primary/5 hover:via-primary/3 hover:to-transparent",
                      selectedRows.has(rowIdx) && "bg-primary/10 border-primary/30",
                      colorClass
                    )}
                  >
                    {/* Checkbox */}
                    <td className="w-12 border-r border-border/30 text-center bg-card/20">
                      <input
                        type="checkbox"
                        checked={selectedRows.has(rowIdx)}
                        onChange={() => toggleRowSelection(rowIdx)}
                        className="cursor-pointer w-4 h-4 accent-primary"
                      />
                    </td>
                    
                    {/* Row Number */}
                    <td className="w-20 border-r border-border/30 px-3 py-2.5 text-xs text-primary/80 text-center font-mono font-semibold bg-card/20">
                      {rowIdx + 1}
                    </td>

                    {/* Data Cells */}
                    {row.getVisibleCells().map(cell => (
                      <td
                        key={cell.id}
                        className="border-r border-border/30 last:border-r-0"
                        style={{ minWidth: cell.column.columnDef.minSize, width: cell.column.getSize() }}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}

                    {/* Actions */}
                    <td className="w-24 text-center border-l border-border/30 bg-card/20 sticky right-0">
                      <div className="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="relative">
                          <button
                            onClick={() => setShowColorPicker(showColorPicker === rowIdx ? null : rowIdx)}
                            className="p-1.5 hover:bg-primary/20 rounded-md transition-colors"
                            title="Color code row"
                          >
                            <Palette size={16} className="text-muted-foreground hover:text-primary transition-colors" />
                          </button>
                          
                          {showColorPicker === rowIdx && (
                            <div className="absolute right-0 top-full mt-1 bg-card border border-primary/30 rounded-lg shadow-2xl p-2 z-20">
                              <div className="grid grid-cols-2 gap-1.5">
                                {COLORS.map(color => (
                                  <button
                                    key={color.name}
                                    onClick={() => setRowColor(rowIdx, color.value)}
                                    className={cn(
                                      "px-3 py-2 text-xs rounded-md transition-all flex items-center justify-between gap-2 border",
                                      color.value ? color.class + ' border-' + color.value + '-500/30' : 'bg-accent border-border hover:bg-accent/80'
                                    )}
                                  >
                                    {color.name}
                                    {rowColors.get(rowIdx) === color.value && <Check size={12} className="text-primary" />}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                        
                        <button
                          onClick={() => handleDeleteRow(rowIdx)}
                          className="p-1.5 hover:bg-destructive/20 rounded-md transition-colors"
                          title="Delete row"
                        >
                          <Trash2 size={16} className="text-destructive" />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  )
}
