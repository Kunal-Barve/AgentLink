'use client'

import { useParams } from 'next/navigation'
import { BeautifulDataGrid } from '@/components/beautiful-data-grid'
import { AppHeader } from '@/components/app-header'
import { AppSidebar } from '@/components/app-sidebar'
import { TabBar } from '@/components/tab-bar'
import { useSheets } from '@/lib/sheets-context'

export default function TabPage() {
  const params = useParams()
  const sheet = params.sheet as string
  const tab = params.tab as string
  const { getTabByName, loading } = useSheets()

  const tabConfig = getTabByName(sheet, tab)

  if (loading) {
    return (
      <>
        <AppHeader />
        <div className="flex h-[calc(100vh-64px)]">
          <AppSidebar />
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent mb-3"></div>
              <p className="text-muted-foreground">Loading...</p>
            </div>
          </div>
        </div>
      </>
    )
  }

  if (!tabConfig) {
    return (
      <>
        <AppHeader />
        <div className="flex h-[calc(100vh-64px)]">
          <AppSidebar />
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <p className="text-lg font-semibold text-white mb-2">Table not found</p>
              <p className="text-sm text-muted-foreground">The table &quot;{tab}&quot; does not exist in &quot;{sheet}&quot;.</p>
            </div>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <AppHeader />
      <div className="flex h-[calc(100vh-64px)]">
        <AppSidebar />
        <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
          <TabBar />
          <BeautifulDataGrid 
            tableName={tabConfig.tableName}
            sheetId={sheet}
            tabName={tab}
          />
        </div>
      </div>
    </>
  )
}
