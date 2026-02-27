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
} from '@tanstack/react-table'
import { DndContext, closestCenter, KeyboardSensor, PointerSensor, useSensor, useSensors } from '@dnd-kit/core'
import { arrayMove, SortableContext, sortableKeyboardCoordinates, horizontalListSortingStrategy } from '@dnd-kit/sortable'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { supabase } from '@/lib/supabase'
import { ChevronDown, ChevronUp, Plus, Trash2, Search, X, Download, Palette, GripVertical, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DataGridProps {
  tableName: string
  sheetId: string
  tabName: string
}

const COLORS = [
  { name: 'None', value: '' },
  { name: 'Red', value: 'bg-red-500/10' },
  { name: 'Orange', value: 'bg-orange-500/10' },
  { name: 'Yellow', value: 'bg-yellow-500/10' },
  { name: 'Green', value: 'bg-green-500/10' },
  { name: 'Blue', value: 'bg-blue-500/10' },
  { name: 'Purple', value: 'bg-purple-500/10' },
  { name: 'Pink', value: 'bg-pink-500/10' },
]

function DraggableColumnHeader({ column, children }: any) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: column.id,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div ref={setNodeRef} style={style} className="flex items-center h-full">
      <div {...attributes} {...listeners} className="cursor-move p-1 hover:bg-accent rounded">
        <GripVertical size={14} className="text-muted-foreground" />
      </div>
      {children}
    </div>
  )
}

export function AdvancedDataGrid({ tableName, sheetId, tabName }: DataGridProps) {
  const [data, setData] = useState<any[]>([])
  const [columns, setColumns] = useState<ColumnDef<any>[]>([])
  const [columnOrder, setColumnOrder] = useState<string[]>([])
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

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

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
          header: ({ column }) => (
            <DraggableColumnHeader column={column}>
              <div className="flex items-center justify-between flex-1 px-2">
                <button
                  onClick={() => column.toggleSorting()}
                  className="flex items-center gap-2 flex-1 text-left"
                >
                  <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide truncate">
                    {key.replace(/_/g, ' ')}
                  </span>
                  {column.getIsSorted() === 'asc' && <ChevronUp size={14} />}
                  {column.getIsSorted() === 'desc' && <ChevronDown size={14} />}
                </button>
                <button
                  onClick={() => setShowColumnFilter(showColumnFilter === key ? null : key)}
                  className="p-1 hover:bg-accent rounded"
                >
                  <ChevronDown size={14} className="text-muted-foreground" />
                </button>
              </div>
            </DraggableColumnHeader>
          ),
          cell: ({ row, column }) => {
            const rowIndex = row.index
            const isEditing = editingCell?.rowIndex === rowIndex && editingCell?.columnId === column.id
            const value = row.getValue(column.id) as string
            
            return (
              <div
                className="h-full px-3 py-2 text-sm flex items-center cursor-text"
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
                    className="w-full h-full px-2 py-1 bg-background border border-primary focus:outline-none text-sm rounded"
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
        setColumnOrder(columnKeys)
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
      alert('Error: ' + err.message)
    }
  }

  function exportToCSV() {
    const headers = columnOrder.join(',')
    const rows = data.map(row => 
      columnOrder.map(col => `"${(row[col] || '').toString().replace(/"/g, '""')}"`).join(',')
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

  function handleDragEnd(event: any) {
    const { active, over } = event
    if (active.id !== over.id) {
      setColumnOrder((items) => {
        const oldIndex = items.indexOf(active.id)
        const newIndex = items.indexOf(over.id)
        return arrayMove(items, oldIndex, newIndex)
      })
    }
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
      columnOrder,
    },
    onColumnOrderChange: setColumnOrder,
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
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-card gap-4">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold">{tableName.replace(/_/g, ' ')}</h2>
          <span className="text-xs text-muted-foreground">{data.length} records</span>
          {selectedRows.size > 0 && (
            <span className="text-xs text-primary">{selectedRows.size} selected</span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* Global Search */}
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search all columns..."
              value={globalFilter}
              onChange={(e) => setGlobalFilter(e.target.value)}
              className="pl-9 pr-8 py-1.5 text-sm bg-background border border-border rounded-md focus:outline-none focus:border-primary w-64"
            />
            {globalFilter && (
              <button
                onClick={() => setGlobalFilter('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {selectedRows.size > 0 && (
            <button
              onClick={handleBulkDelete}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-destructive/10 text-destructive rounded-md hover:bg-destructive/20 transition-colors"
            >
              <Trash2 size={16} />
              Delete Selected
            </button>
          )}
          
          <button
            onClick={exportToCSV}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-accent text-foreground rounded-md hover:bg-accent/80 transition-colors"
          >
            <Download size={16} />
            Export CSV
          </button>
          
          <button
            onClick={handleAddRow}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            <Plus size={16} />
            Add Record
          </button>
        </div>
      </div>

      {/* Data Grid with Horizontal Scroll */}
      <div className="flex-1 overflow-auto">
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <table className="w-full border-collapse" style={{ minWidth: '100%' }}>
            <thead className="sticky top-0 z-10 bg-card border-b border-border">
              <tr>
                {/* Checkbox Column */}
                <th className="w-12 border-r border-border bg-card">
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
                    className="cursor-pointer"
                  />
                </th>
                
                {/* Row Number Column */}
                <th className="w-16 border-r border-border bg-card px-3 py-2 text-xs font-medium text-muted-foreground text-center">
                  #
                </th>

                {/* Data Columns */}
                <SortableContext items={columnOrder} strategy={horizontalListSortingStrategy}>
                  {table.getHeaderGroups().map(headerGroup => (
                    headerGroup.headers.filter(header => columnOrder.includes(header.id)).map((header) => (
                      <th
                        key={header.id}
                        className="relative border-r border-border last:border-r-0 h-10 bg-card"
                        style={{ width: header.getSize(), minWidth: header.column.columnDef.minSize }}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        
                        {/* Column Filter Dropdown */}
                        {showColumnFilter === header.id && (
                          <div className="absolute top-full left-0 mt-1 bg-card border border-border rounded-md shadow-lg p-2 z-20 w-48">
                            <input
                              type="text"
                              placeholder="Filter..."
                              value={(columnFilters.find(f => f.id === header.id)?.value as string) || ''}
                              onChange={(e) => {
                                const value = e.target.value
                                setColumnFilters(prev => 
                                  value
                                    ? [...prev.filter(f => f.id !== header.id), { id: header.id, value }]
                                    : prev.filter(f => f.id !== header.id)
                                )
                              }}
                              className="w-full px-2 py-1 text-sm bg-background border border-border rounded focus:outline-none focus:border-primary"
                            />
                          </div>
                        )}
                        
                        {/* Resize Handle */}
                        <div
                          onMouseDown={header.getResizeHandler()}
                          onTouchStart={header.getResizeHandler()}
                          className={cn(
                            "absolute right-0 top-0 h-full w-1 cursor-col-resize select-none touch-none hover:bg-primary transition-colors",
                            header.column.getIsResizing() && 'bg-primary'
                          )}
                        />
                      </th>
                    ))
                  ))}
                </SortableContext>

                {/* Actions Column */}
                <th className="w-20 bg-card border-l border-border"></th>
              </tr>
            </thead>
            
            <tbody>
              {table.getRowModel().rows.map((row, rowIdx) => (
                <tr
                  key={row.id}
                  className={cn(
                    "group border-b border-border hover:bg-accent/50 transition-colors",
                    selectedRows.has(rowIdx) && "bg-primary/10",
                    rowColors.get(rowIdx)
                  )}
                >
                  {/* Checkbox */}
                  <td className="w-12 border-r border-border text-center">
                    <input
                      type="checkbox"
                      checked={selectedRows.has(rowIdx)}
                      onChange={() => toggleRowSelection(rowIdx)}
                      className="cursor-pointer"
                    />
                  </td>
                  
                  {/* Row Number (1-indexed) */}
                  <td className="w-16 border-r border-border px-3 py-2 text-xs text-muted-foreground text-center font-mono">
                    {rowIdx + 1}
                  </td>

                  {/* Data Cells */}
                  {row.getVisibleCells()
                    .filter(cell => columnOrder.includes(cell.column.id))
                    .sort((a, b) => columnOrder.indexOf(a.column.id) - columnOrder.indexOf(b.column.id))
                    .map(cell => (
                      <td
                        key={cell.id}
                        className="border-r border-border last:border-r-0 h-10"
                        style={{ width: cell.column.getSize(), minWidth: cell.column.columnDef.minSize }}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}

                  {/* Actions */}
                  <td className="w-20 text-center border-l border-border">
                    <div className="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="relative">
                        <button
                          onClick={() => setShowColorPicker(showColorPicker === rowIdx ? null : rowIdx)}
                          className="p-1 hover:bg-accent rounded"
                          title="Color code row"
                        >
                          <Palette size={14} className="text-muted-foreground" />
                        </button>
                        
                        {showColorPicker === rowIdx && (
                          <div className="absolute right-0 top-full mt-1 bg-card border border-border rounded-md shadow-lg p-2 z-20">
                            <div className="grid grid-cols-2 gap-1">
                              {COLORS.map(color => (
                                <button
                                  key={color.name}
                                  onClick={() => setRowColor(rowIdx, color.value)}
                                  className={cn(
                                    "px-3 py-1.5 text-xs rounded hover:opacity-80 transition-opacity flex items-center gap-2",
                                    color.value || 'bg-accent'
                                  )}
                                >
                                  {color.name}
                                  {rowColors.get(rowIdx) === color.value && <Check size={12} />}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      
                      <button
                        onClick={() => handleDeleteRow(rowIdx)}
                        className="p-1 hover:bg-destructive/10 rounded"
                        title="Delete row"
                      >
                        <Trash2 size={14} className="text-destructive" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </DndContext>
      </div>

      {/* Keyboard Shortcuts Help */}
      <div className="px-4 py-2 border-t border-border bg-card text-xs text-muted-foreground flex items-center gap-4">
        <span><kbd className="px-1.5 py-0.5 bg-accent rounded">Ctrl+A</kbd> Select All</span>
        <span><kbd className="px-1.5 py-0.5 bg-accent rounded">Ctrl+E</kbd> Export</span>
        <span><kbd className="px-1.5 py-0.5 bg-accent rounded">Del</kbd> Delete Selected</span>
        <span><kbd className="px-1.5 py-0.5 bg-accent rounded">Esc</kbd> Clear Selection</span>
      </div>
    </div>
  )
}
