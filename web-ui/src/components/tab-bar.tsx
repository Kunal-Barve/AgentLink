'use client'

import Link from 'next/link'
import { useParams } from 'next/navigation'
import { useSheets } from '@/lib/sheets-context'
import { cn } from '@/lib/utils'

export function TabBar() {
  const params = useParams()
  const sheetId = params.sheet as string
  const currentTab = params.tab as string
  
  const { getSheetById } = useSheets()
  const sheet = getSheetById(sheetId)
  
  if (!sheet) return null

  if (sheet.tabs.length <= 1) return null
  
  return (
    <div className="border-b border-border bg-card/80 backdrop-blur-sm">
      <div className="flex items-center px-4 overflow-x-auto">
        {sheet.tabs.map((tab) => {
          const isActive = currentTab === tab.name
          
          return (
            <Link
              key={tab.name}
              href={`/${sheetId}/${tab.name}`}
              className={cn(
                "px-4 py-2.5 text-sm font-medium border-b-2 transition-all whitespace-nowrap",
                isActive
                  ? "border-primary text-primary bg-primary/10"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:border-white/20"
              )}
            >
              {tab.displayName}
            </Link>
          )
        })}
      </div>
    </div>
  )
}
