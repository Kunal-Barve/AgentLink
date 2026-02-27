'use client'

import { usePathname } from 'next/navigation'
import { AppHeader } from '@/components/app-header'
import { AppSidebar } from '@/components/app-sidebar'

export function LayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const showLayout = pathname !== '/login'

  if (!showLayout) {
    return <>{children}</>
  }

  return (
    <>
      <AppHeader />
      <div className="flex">
        <AppSidebar />
        {children}
      </div>
    </>
  )
}
