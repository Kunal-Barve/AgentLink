'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { SHEETS_CONFIG } from '@/lib/sheet-config'
import { cn } from '@/lib/utils'
import { Database } from 'lucide-react'

export function SheetNav() {
  const pathname = usePathname()
  
  return (
    <div className="w-64 border-r border-border bg-card h-screen overflow-y-auto flex flex-col">
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-primary" />
          <div>
            <h1 className="text-sm font-semibold">AgentLink</h1>
            <p className="text-xs text-muted-foreground">Database</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 p-3">
        <div className="space-y-1">
          {SHEETS_CONFIG.map((sheet) => {
            const isActive = pathname.startsWith(`/${sheet.id}`)
            
            return (
              <Link
                key={sheet.id}
                href={`/${sheet.id}/${sheet.tabs[0].name}`}
                className={cn(
                  "flex items-center justify-between px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                  isActive 
                    ? "bg-primary/10 text-primary" 
                    : "text-foreground hover:bg-accent"
                )}
              >
                <span className="truncate">{sheet.name}</span>
                <span className="text-xs text-muted-foreground ml-2">{sheet.tabs.length}</span>
              </Link>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
