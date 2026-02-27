'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Database, Settings, ChevronDown, ChevronRight } from 'lucide-react'
import { SHEETS_CONFIG } from '@/lib/sheet-config'
import { cn } from '@/lib/utils'

export function AppSidebar() {
  const pathname = usePathname()
  const [isDatabaseOpen, setIsDatabaseOpen] = useState(true)

  return (
    <aside className="hidden md:flex w-64 border-r border-white/5 h-[calc(100vh-64px)] sticky top-16 p-6 flex-col shrink-0 overflow-y-auto">
      <nav className="space-y-1 flex-1">
        <Link
          href="/"
          className={cn(
            "flex items-center space-x-3 px-3 py-2 rounded-lg font-medium transition-all",
            pathname === "/" 
              ? "bg-white/5 text-white" 
              : "text-slate-400 hover:bg-white/5 hover:text-white"
          )}
        >
          <Home size={20} />
          <span>Home</span>
        </Link>

        <div>
          <button
            onClick={() => setIsDatabaseOpen(!isDatabaseOpen)}
            className="w-full flex items-center justify-between px-3 py-2 text-slate-400 hover:bg-white/5 hover:text-white rounded-lg transition-all"
          >
            <div className="flex items-center space-x-3">
              <Database size={20} />
              <span>Databases</span>
            </div>
            {isDatabaseOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>

          {isDatabaseOpen && (
            <div className="ml-6 mt-1 space-y-1">
              {SHEETS_CONFIG.map((sheet) => (
                <Link
                  key={sheet.id}
                  href={`/${sheet.id}/${sheet.tabs[0].name}`}
                  className={cn(
                    "flex items-center space-x-3 px-3 py-1.5 text-sm rounded-lg transition-all",
                    pathname.startsWith(`/${sheet.id}`)
                      ? "text-primary bg-primary/10"
                      : "text-slate-400 hover:bg-white/5 hover:text-white"
                  )}
                >
                  <span className={cn(
                    "rounded-full shrink-0",
                    pathname.startsWith(`/${sheet.id}`)
                      ? "h-2 w-2 bg-blue-500 shadow-[0_0_6px_rgba(59,130,246,0.6)]"
                      : "h-1.5 w-1.5 bg-slate-500"
                  )}></span>
                  <span className="truncate">{sheet.name}</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </nav>

      <div className="mt-auto pt-6">
        <Link
          href="/settings"
          className="flex items-center space-x-3 px-3 py-2 text-slate-400 hover:bg-white/5 hover:text-white rounded-lg transition-all"
        >
          <Settings size={20} />
          <span>Settings</span>
        </Link>

        <div className="mt-6 bg-primary/5 p-4 rounded-xl border border-primary/20">
          <p className="text-xs font-semibold text-primary mb-1">Advanced Mode</p>
          <p className="text-[11px] text-slate-400 mb-3 leading-relaxed">
            System healthy. Supabase syncing enabled.
          </p>
          <button className="w-full bg-white/10 text-white py-1.5 rounded-lg text-[11px] font-bold border border-white/10 hover:bg-white/20 transition-colors">
            Status Dashboard
          </button>
        </div>
      </div>
    </aside>
  )
}
