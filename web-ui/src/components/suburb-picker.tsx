'use client'

import { useState, useEffect, useRef } from 'react'
import { Search, X, MapPin, Plus } from 'lucide-react'
import { cn } from '@/lib/utils'

// State color mapping — pale bg for dark UI, with matching text colors
const STATE_COLORS: Record<string, { bg: string; text: string; border: string; badge: string }> = {
  NSW: { bg: 'bg-blue-500/15', text: 'text-blue-300', border: 'border-blue-500/30', badge: 'bg-blue-500/20' },
  VIC: { bg: 'bg-purple-500/15', text: 'text-purple-300', border: 'border-purple-500/30', badge: 'bg-purple-500/20' },
  QLD: { bg: 'bg-amber-500/15', text: 'text-amber-300', border: 'border-amber-500/30', badge: 'bg-amber-500/20' },
  SA:  { bg: 'bg-rose-500/15', text: 'text-rose-300', border: 'border-rose-500/30', badge: 'bg-rose-500/20' },
  WA:  { bg: 'bg-cyan-500/15', text: 'text-cyan-300', border: 'border-cyan-500/30', badge: 'bg-cyan-500/20' },
  TAS: { bg: 'bg-emerald-500/15', text: 'text-emerald-300', border: 'border-emerald-500/30', badge: 'bg-emerald-500/20' },
  NT:  { bg: 'bg-green-500/15', text: 'text-green-300', border: 'border-green-500/30', badge: 'bg-green-500/20' },
  ACT: { bg: 'bg-pink-500/15', text: 'text-pink-300', border: 'border-pink-500/30', badge: 'bg-pink-500/20' },
}

const DEFAULT_COLOR = { bg: 'bg-slate-500/15', text: 'text-slate-300', border: 'border-slate-500/30', badge: 'bg-slate-500/20' }

export function getStateColor(state: string) {
  return STATE_COLORS[state.toUpperCase()] || DEFAULT_COLOR
}

/**
 * Renders a single suburb badge with state-specific color coding.
 * Value format: "SUBURB | STATE | POSTCODE"
 */
export function SuburbBadge({ value, onRemove }: { value: string; onRemove?: () => void }) {
  if (!value) return null

  const parts = value.split('|').map(s => s.trim())
  if (parts.length < 2) return <span className="text-sm">{value}</span>

  const state = parts[1] || ''
  const color = getStateColor(state)

  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold whitespace-nowrap",
      color.badge, color.text, "border", color.border
    )}>
      <MapPin size={10} className="shrink-0" />
      <span className="truncate max-w-[180px]">{value}</span>
      {onRemove && (
        <button
          onClick={(e) => { e.stopPropagation(); onRemove(); }}
          className="ml-0.5 hover:bg-white/10 rounded p-0.5 transition-colors"
        >
          <X size={10} />
        </button>
      )}
    </span>
  )
}

/**
 * Sort values by state code so same-state suburbs are grouped together.
 */
function sortByState(values: string[]): { val: string; origIdx: number }[] {
  return values
    .map((val, origIdx) => ({ val, origIdx }))
    .sort((a, b) => {
      const stateA = a.val.split('|')[1]?.trim() || ''
      const stateB = b.val.split('|')[1]?.trim() || ''
      if (stateA !== stateB) return stateA.localeCompare(stateB)
      return a.val.localeCompare(b.val)
    })
}

/**
 * Renders the multi-value suburb cell display.
 * Fixed height — shows badges inline, grouped by state.
 * When overflowed, shows a "+N more" button that opens a popover.
 */
export function SuburbCellDisplay({ values, onRemove, onAdd }: {
  values: string[]
  onRemove: (index: number) => void
  onAdd: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const expandRef = useRef<HTMLDivElement>(null)

  // Close popover on outside click
  useEffect(() => {
    if (!expanded) return
    function handleClick(e: MouseEvent) {
      if (expandRef.current && !expandRef.current.contains(e.target as Node)) {
        setExpanded(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [expanded])

  if (!values || values.length === 0) {
    return (
      <button
        onClick={(e) => { e.stopPropagation(); onAdd(); }}
        className="text-muted-foreground italic text-xs hover:text-primary transition-colors"
      >
        Click to add suburbs...
      </button>
    )
  }

  const sorted = sortByState(values)

  return (
    <div className="relative w-full">
      {/* Compact inline view — single line, overflow hidden */}
      <div className="flex items-center gap-1 overflow-hidden max-h-[24px]">
        {sorted.slice(0, 2).map(({ val, origIdx }) => (
          <SuburbBadge key={`${val}-${origIdx}`} value={val} onRemove={() => onRemove(origIdx)} />
        ))}
        {values.length > 2 && (
          <button
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}
            className="shrink-0 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold text-primary bg-primary/10 hover:bg-primary/20 border border-primary/20 transition-colors"
          >
            +{values.length - 2} more
          </button>
        )}
        {values.length <= 2 && (
          <button
            onClick={(e) => { e.stopPropagation(); onAdd(); }}
            className="shrink-0 inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-semibold text-slate-400 hover:text-primary hover:bg-primary/10 border border-dashed border-white/10 hover:border-primary/30 transition-all"
          >
            <Plus size={9} />
          </button>
        )}
      </div>

      {/* Expanded popover — shows all suburbs grouped by state */}
      {expanded && (
        <div
          ref={expandRef}
          className="absolute top-full left-0 mt-1 w-80 bg-card border border-white/10 rounded-xl shadow-2xl z-[100] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="px-3 py-2 border-b border-white/5 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400">{values.length} suburbs</span>
            <div className="flex items-center gap-2">
              <button
                onClick={(e) => { e.stopPropagation(); onAdd(); }}
                className="text-[10px] font-semibold text-primary hover:text-white bg-primary/10 hover:bg-primary/20 px-2 py-1 rounded transition-colors"
              >
                + Add
              </button>
              <button onClick={() => setExpanded(false)} className="text-slate-500 hover:text-white">
                <X size={14} />
              </button>
            </div>
          </div>
          <div className="max-h-48 overflow-y-auto p-2">
            <div className="flex flex-col gap-1">
              {sorted.map(({ val, origIdx }) => (
                <SuburbBadge key={`${val}-${origIdx}`} value={val} onRemove={() => onRemove(origIdx)} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

interface SuburbPickerProps {
  values: string[]
  onChange: (values: string[]) => void
  onClose: () => void
}

type Step = 'state' | 'suburb' | 'postcode'

export function SuburbPicker({ values, onChange, onClose }: SuburbPickerProps) {
  const [step, setStep] = useState<Step>('state')
  const [selectedState, setSelectedState] = useState('')
  const [selectedSuburb, setSelectedSuburb] = useState('')

  // Data
  const [states, setStates] = useState<string[]>([])
  const [suburbs, setSuburbs] = useState<string[]>([])
  const [postcodes, setPostcodes] = useState<string[]>([])

  // Search & loading
  const [suburbSearch, setSuburbSearch] = useState('')
  const [loadingStates, setLoadingStates] = useState(false)
  const [loadingSuburbs, setLoadingSuburbs] = useState(false)
  const [loadingPostcodes, setLoadingPostcodes] = useState(false)

  // Manual entry
  const [showManualSuburb, setShowManualSuburb] = useState(false)
  const [showManualPostcode, setShowManualPostcode] = useState(false)
  const [manualSuburb, setManualSuburb] = useState('')
  const [manualPostcode, setManualPostcode] = useState('')

  const containerRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const searchTimerRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    fetchStates()
  }, [])

  useEffect(() => {
    if (step === 'suburb') {
      setTimeout(() => searchInputRef.current?.focus(), 50)
    }
  }, [step])

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [onClose])

  async function fetchStates() {
    setLoadingStates(true)
    try {
      const res = await fetch('/api/suburbs?action=states')
      const data = await res.json()
      setStates(data.states || [])
    } catch (e) {
      console.error('Failed to fetch states:', e)
    } finally {
      setLoadingStates(false)
    }
  }

  async function fetchSuburbs(state: string, search: string = '') {
    setLoadingSuburbs(true)
    try {
      const params = new URLSearchParams({ action: 'suburbs', state })
      if (search) params.set('search', search)
      const res = await fetch(`/api/suburbs?${params}`)
      const data = await res.json()
      setSuburbs(data.suburbs || [])
    } catch (e) {
      console.error('Failed to fetch suburbs:', e)
    } finally {
      setLoadingSuburbs(false)
    }
  }

  async function fetchPostcodes(state: string, suburb: string) {
    setLoadingPostcodes(true)
    try {
      const params = new URLSearchParams({ action: 'postcodes', state, suburb })
      const res = await fetch(`/api/suburbs?${params}`)
      const data = await res.json()
      setPostcodes(data.postcodes || [])
    } catch (e) {
      console.error('Failed to fetch postcodes:', e)
    } finally {
      setLoadingPostcodes(false)
    }
  }

  function handleStateSelect(state: string) {
    setSelectedState(state)
    setStep('suburb')
    setSuburbSearch('')
    setSuburbs([])
    fetchSuburbs(state)
  }

  function handleSuburbSearch(query: string) {
    setSuburbSearch(query)
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current)
    searchTimerRef.current = setTimeout(() => {
      fetchSuburbs(selectedState, query)
    }, 300)
  }

  function handleSuburbSelect(suburb: string) {
    setSelectedSuburb(suburb)
    setStep('postcode')
    fetchPostcodes(selectedState, suburb)
  }

  function handleManualSuburbConfirm() {
    if (manualSuburb.trim()) {
      handleSuburbSelect(manualSuburb.trim().toUpperCase())
      setShowManualSuburb(false)
    }
  }

  function handlePostcodeSelect(postcode: string) {
    const newEntry = `${selectedSuburb.toUpperCase()} | ${selectedState.toUpperCase()} | ${postcode}`
    // Check for duplicates
    if (values.includes(newEntry)) {
      // Reset to add another without closing
      resetToState()
      return
    }
    onChange([...values, newEntry])
    // Reset picker to allow adding more
    resetToState()
  }

  function handleManualPostcodeConfirm() {
    if (manualPostcode.trim()) {
      handlePostcodeSelect(manualPostcode.trim())
      setShowManualPostcode(false)
    }
  }

  function resetToState() {
    setStep('state')
    setSelectedState('')
    setSelectedSuburb('')
    setSuburbSearch('')
    setSuburbs([])
    setPostcodes([])
    setShowManualSuburb(false)
    setShowManualPostcode(false)
    setManualSuburb('')
    setManualPostcode('')
  }

  function handleBack() {
    if (step === 'postcode') {
      setStep('suburb')
      setSelectedSuburb('')
      setPostcodes([])
    } else if (step === 'suburb') {
      setStep('state')
      setSelectedState('')
      setSuburbs([])
      setSuburbSearch('')
    }
  }

  // Check if a suburb entry already exists
  function isAlreadyAdded(suburb: string, state: string, postcode: string) {
    const key = `${suburb.toUpperCase()} | ${state.toUpperCase()} | ${postcode}`
    return values.includes(key)
  }

  return (
    <div
      ref={containerRef}
      className="absolute top-full left-0 mt-1 w-80 bg-card border border-white/10 rounded-xl shadow-2xl z-[100] overflow-hidden"
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={resetToState}
            className={cn("font-semibold transition-colors", step === 'state' ? 'text-primary' : 'text-slate-400 hover:text-white')}
          >
            State
          </button>
          {selectedState && (
            <>
              <span className="text-slate-600">/</span>
              <button
                onClick={() => { setStep('suburb'); setSelectedSuburb(''); }}
                className={cn("font-semibold transition-colors", step === 'suburb' ? 'text-primary' : 'text-slate-400 hover:text-white')}
              >
                {selectedState}
              </button>
            </>
          )}
          {selectedSuburb && (
            <>
              <span className="text-slate-600">/</span>
              <span className="font-semibold text-primary truncate max-w-[100px]">{selectedSuburb}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          {values.length > 0 && (
            <span className="text-[10px] font-bold text-primary bg-primary/10 px-1.5 py-0.5 rounded">
              {values.length} selected
            </span>
          )}
          {step !== 'state' ? (
            <button onClick={handleBack} className="text-slate-500 hover:text-white transition-colors" title="Go back">
              <X size={14} />
            </button>
          ) : (
            <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors" title="Close">
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Current selections (shown at top when not empty) */}
      {values.length > 0 && (
        <div className="px-3 py-2 border-b border-white/5 max-h-24 overflow-y-auto">
          <div className="flex flex-wrap gap-1">
            {values.map((val, idx) => (
              <SuburbBadge
                key={`${val}-${idx}`}
                value={val}
                onRemove={() => onChange(values.filter((_, i) => i !== idx))}
              />
            ))}
          </div>
        </div>
      )}

      {/* Step: Select State */}
      {step === 'state' && (
        <div className="p-2 max-h-64 overflow-y-auto">
          <div className="px-2 py-1.5 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            Add Suburb — Select State
          </div>
          {loadingStates ? (
            <div className="flex items-center justify-center py-6">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-r-transparent"></div>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-1">
              {states.map(state => {
                const color = getStateColor(state)
                return (
                  <button
                    key={state}
                    onClick={() => handleStateSelect(state)}
                    className={cn(
                      "flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-semibold transition-all",
                      "hover:scale-[1.02]",
                      color.bg, color.text, "border", color.border,
                      "hover:brightness-125"
                    )}
                  >
                    <span className={cn("w-2 h-2 rounded-full", color.text.replace('text-', 'bg-'))} />
                    {state}
                  </button>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Step: Select Suburb */}
      {step === 'suburb' && (
        <div className="flex flex-col max-h-80">
          <div className="p-2 border-b border-white/5">
            <div className="flex items-center bg-white/5 rounded-lg px-3 py-2 border border-white/10">
              <Search size={14} className="text-slate-500 mr-2 shrink-0" />
              <input
                ref={searchInputRef}
                type="text"
                value={suburbSearch}
                onChange={(e) => handleSuburbSearch(e.target.value)}
                placeholder="Search suburb..."
                className="bg-transparent border-none focus:ring-0 text-sm w-full placeholder-slate-500 text-white focus:outline-none"
              />
              {suburbSearch && (
                <button onClick={() => { setSuburbSearch(''); fetchSuburbs(selectedState); }} className="text-slate-500 hover:text-white">
                  <X size={12} />
                </button>
              )}
            </div>
          </div>
          <div className="overflow-y-auto max-h-52 p-1">
            {loadingSuburbs ? (
              <div className="flex items-center justify-center py-6">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-r-transparent"></div>
              </div>
            ) : suburbs.length > 0 ? (
              suburbs.map(suburb => (
                <button
                  key={suburb}
                  onClick={() => handleSuburbSelect(suburb)}
                  className="w-full text-left px-3 py-2 text-sm text-slate-300 hover:bg-white/5 hover:text-white rounded-lg transition-colors truncate"
                >
                  {suburb}
                </button>
              ))
            ) : (
              <div className="px-3 py-4 text-center text-xs text-slate-500">
                {suburbSearch ? 'No suburbs found' : 'Type to search suburbs'}
              </div>
            )}
          </div>
          <div className="p-2 border-t border-white/5">
            {showManualSuburb ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={manualSuburb}
                  onChange={(e) => setManualSuburb(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleManualSuburbConfirm()}
                  placeholder="Enter suburb name..."
                  autoFocus
                  className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary"
                />
                <button onClick={handleManualSuburbConfirm} className="px-3 py-1.5 bg-primary text-white text-xs font-semibold rounded-lg hover:bg-primary/80">
                  OK
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowManualSuburb(true)}
                className="w-full text-left px-3 py-2 text-xs font-medium text-primary hover:bg-primary/10 rounded-lg transition-colors"
              >
                + Other (type manually)
              </button>
            )}
          </div>
        </div>
      )}

      {/* Step: Select Postcode */}
      {step === 'postcode' && (
        <div className="flex flex-col max-h-64">
          <div className="px-4 py-2 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            Select Postcode for {selectedSuburb}, {selectedState}
          </div>
          <div className="overflow-y-auto p-1">
            {loadingPostcodes ? (
              <div className="flex items-center justify-center py-6">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-r-transparent"></div>
              </div>
            ) : postcodes.length > 0 ? (
              postcodes.map(pc => {
                const alreadyAdded = isAlreadyAdded(selectedSuburb, selectedState, pc)
                return (
                  <button
                    key={pc}
                    onClick={() => !alreadyAdded && handlePostcodeSelect(pc)}
                    className={cn(
                      "w-full text-left px-3 py-2.5 text-sm rounded-lg transition-colors flex items-center justify-between",
                      alreadyAdded
                        ? "text-slate-500 cursor-default"
                        : "text-slate-300 hover:bg-white/5 hover:text-white"
                    )}
                  >
                    <span className="font-mono">{pc}</span>
                    {alreadyAdded && <span className="text-[10px] text-primary">Added</span>}
                  </button>
                )
              })
            ) : (
              <div className="px-3 py-4 text-center text-xs text-slate-500">No postcodes found</div>
            )}
          </div>
          <div className="p-2 border-t border-white/5">
            {showManualPostcode ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={manualPostcode}
                  onChange={(e) => setManualPostcode(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleManualPostcodeConfirm()}
                  placeholder="Enter postcode..."
                  autoFocus
                  className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-primary"
                />
                <button onClick={handleManualPostcodeConfirm} className="px-3 py-1.5 bg-primary text-white text-xs font-semibold rounded-lg hover:bg-primary/80">
                  OK
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowManualPostcode(true)}
                className="w-full text-left px-3 py-2 text-xs font-medium text-primary hover:bg-primary/10 rounded-lg transition-colors"
              >
                + Other (type manually)
              </button>
            )}
          </div>
        </div>
      )}

      {/* Footer: Back + Done */}
      <div className="px-3 py-2 border-t border-white/5 flex items-center justify-between">
        {step !== 'state' ? (
          <button onClick={handleBack} className="text-xs text-slate-400 hover:text-white transition-colors">
            ← Back
          </button>
        ) : <span />}
        <button
          onClick={onClose}
          className="text-xs font-semibold text-primary hover:text-white bg-primary/10 hover:bg-primary/20 px-3 py-1.5 rounded-lg transition-colors"
        >
          Done
        </button>
      </div>
    </div>
  )
}
