import { notFound } from 'next/navigation'
import { getTabByName } from '@/lib/sheet-config'
import { BeautifulDataGrid } from '@/components/beautiful-data-grid'
import { AppHeader } from '@/components/app-header'
import { AppSidebar } from '@/components/app-sidebar'
import { TabBar } from '@/components/tab-bar'

interface PageProps {
  params: Promise<{
    sheet: string
    tab: string
  }>
}

export default async function TabPage({ params }: PageProps) {
  const { sheet, tab } = await params
  const tabConfig = getTabByName(sheet, tab)

  if (!tabConfig) {
    notFound()
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
