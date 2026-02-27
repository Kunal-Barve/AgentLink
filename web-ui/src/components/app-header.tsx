'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import { Database, Search, Bell, X } from 'lucide-react'
import { SHEETS_CONFIG } from '@/lib/sheet-config'

export function AppHeader() {
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('')
  const [showResults, setShowResults] = useState(false)
  const searchRef = useRef<HTMLDivElement>(null)

  const filteredSheets = searchQuery.trim()
    ? SHEETS_CONFIG.filter(sheet =>
        sheet.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        sheet.tabs.some(tab => tab.displayName.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : []

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowResults(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        const input = searchRef.current?.querySelector('input')
        input?.focus()
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 sticky top-0 z-50 bg-black/60 backdrop-blur-xl">
      <Link href="/" className="flex items-center hover:opacity-80 transition-opacity">
        <Image
          src="/logo-dark.png"
          alt="AgentLink"
          width={160}
          height={40}
          className="h-8 w-auto object-contain"
          priority
        />
      </Link>

      <div className="flex items-center space-x-6">
        <div className="hidden md:block relative" ref={searchRef}>
          <div className="flex items-center bg-white/5 rounded-full px-4 py-1.5 border border-white/5">
            <Search size={16} className="text-slate-500 mr-2" />
            <input
              className="bg-transparent border-none focus:ring-0 text-sm w-48 placeholder-slate-500 text-white focus:outline-none"
              placeholder="Search databases..."
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value)
                setShowResults(true)
              }}
              onFocus={() => searchQuery.trim() && setShowResults(true)}
            />
            {searchQuery ? (
              <button onClick={() => { setSearchQuery(''); setShowResults(false) }} className="text-slate-500 hover:text-white transition-colors">
                <X size={14} />
              </button>
            ) : (
              <span className="text-[10px] font-semibold text-slate-500 border border-white/10 px-1.5 rounded-md ml-2 uppercase">
                Ctrl K
              </span>
            )}
          </div>

          {showResults && searchQuery.trim() && (
            <div className="absolute top-full mt-2 right-0 w-80 bg-card border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
              {filteredSheets.length > 0 ? (
                <div className="py-2">
                  {filteredSheets.map(sheet => (
                    <div key={sheet.id}>
                      <button
                        onClick={() => {
                          router.push(`/${sheet.id}/${sheet.tabs[0].name}`)
                          setSearchQuery('')
                          setShowResults(false)
                        }}
                        className="w-full text-left px-4 py-2.5 hover:bg-white/5 transition-colors flex items-center gap-3"
                      >
                        <Database size={16} className="text-primary shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-white truncate">{sheet.name}</p>
                          <p className="text-xs text-slate-500">{sheet.tabs.length} tables</p>
                        </div>
                      </button>
                      {sheet.tabs
                        .filter(tab => tab.displayName.toLowerCase().includes(searchQuery.toLowerCase()))
                        .map(tab => (
                          <button
                            key={tab.name}
                            onClick={() => {
                              router.push(`/${sheet.id}/${tab.name}`)
                              setSearchQuery('')
                              setShowResults(false)
                            }}
                            className="w-full text-left pl-12 pr-4 py-2 hover:bg-white/5 transition-colors"
                          >
                            <p className="text-xs text-slate-400">{tab.displayName}</p>
                          </button>
                        ))}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="px-4 py-6 text-center">
                  <p className="text-sm text-slate-500">No databases found</p>
                </div>
              )}
            </div>
          )}
        </div>

        <button className="p-2 hover:bg-white/5 rounded-full transition-colors">
          <Bell size={20} className="text-slate-400" />
        </button>

        <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-primary to-blue-400 flex items-center justify-center text-white font-semibold text-xs border border-white/20 shadow-sm">
          JD
        </div>
      </div>
    </header>
  )
}
