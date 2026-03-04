'use client'

import { useState } from 'react'
import { X, Plus, Trash2, Database, Loader2 } from 'lucide-react'

interface Column {
  name: string
  type: string
}

interface CreateDatabaseModalProps {
  isOpen: boolean
  onClose: () => void
  onCreated: (tableName: string, displayName: string, columns: Column[]) => void
}

const COLUMN_TYPES = [
  { value: 'text', label: 'Text' },
  { value: 'number', label: 'Number' },
  { value: 'boolean', label: 'Yes/No' },
  { value: 'date', label: 'Date' },
]

export function CreateDatabaseModal({ isOpen, onClose, onCreated }: CreateDatabaseModalProps) {
  const [dbName, setDbName] = useState('')
  const [columns, setColumns] = useState<Column[]>([
    { name: '', type: 'text' },
  ])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  function addColumn() {
    setColumns(prev => [...prev, { name: '', type: 'text' }])
  }

  function removeColumn(index: number) {
    if (columns.length <= 1) return
    setColumns(prev => prev.filter((_, i) => i !== index))
  }

  function updateColumn(index: number, field: keyof Column, value: string) {
    setColumns(prev => prev.map((col, i) => i === index ? { ...col, [field]: value } : col))
  }

  async function handleCreate() {
    if (!dbName.trim()) {
      setError('Please enter a database name')
      return
    }

    const validColumns = columns.filter(c => c.name.trim())
    if (validColumns.length === 0) {
      setError('Please add at least one column')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const res = await fetch('/api/create-table', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tableName: dbName.trim(),
          columns: validColumns,
        }),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.error || 'Failed to create database')
      }

      onCreated(data.tableName, dbName.trim(), validColumns)
      setDbName('')
      setColumns([{ name: '', type: 'text' }])
      onClose()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      
      <div className="relative bg-card border border-white/10 rounded-2xl w-full max-w-lg mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 bg-primary/10 rounded-xl flex items-center justify-center">
              <Database size={20} className="text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Create New Database</h2>
              <p className="text-xs text-slate-400">Define your table structure</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg transition-colors">
            <X size={20} className="text-slate-400" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-5 max-h-[60vh] overflow-y-auto">
          {/* Database Name */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Database Name</label>
            <input
              type="text"
              value={dbName}
              onChange={(e) => setDbName(e.target.value)}
              placeholder="e.g. Agent Performance"
              className="w-full px-4 py-2.5 bg-background border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 text-sm"
              autoFocus
            />
            {dbName.trim() && (
              <p className="text-xs text-slate-500 mt-1">
                Table name: <code className="text-primary/80">{dbName.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')}</code>
              </p>
            )}
          </div>

          {/* Columns */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-slate-300">Columns</label>
              <button
                onClick={addColumn}
                className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors"
              >
                <Plus size={14} />
                Add Column
              </button>
            </div>

            <div className="space-y-2">
              {columns.map((col, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={col.name}
                    onChange={(e) => updateColumn(idx, 'name', e.target.value)}
                    placeholder="Column name"
                    className="flex-1 px-3 py-2 bg-background border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-primary text-sm"
                  />
                  <select
                    value={col.type}
                    onChange={(e) => updateColumn(idx, 'type', e.target.value)}
                    className="px-3 py-2 bg-background border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:border-primary"
                  >
                    {COLUMN_TYPES.map(t => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => removeColumn(idx)}
                    disabled={columns.length <= 1}
                    className="p-2 hover:bg-destructive/20 rounded-lg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <Trash2 size={14} className="text-destructive" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {error && (
            <div className="px-4 py-3 bg-destructive/10 border border-destructive/20 rounded-lg">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-white/10 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2 text-sm font-semibold bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 shadow-lg shadow-primary/20"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Plus size={16} />
                Create Database
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
