'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useSheets } from '@/lib/sheets-context'
import { Plus, MoreHorizontal, Filter, Database } from 'lucide-react'
import { AppHeader } from '@/components/app-header'
import { AppSidebar } from '@/components/app-sidebar'
import { CreateDatabaseModal } from '@/components/create-database-modal'

const CARD_COLORS = [
  { bgColor: 'bg-blue-500/10', textColor: 'text-blue-400', borderColor: 'border-blue-500/20' },
  { bgColor: 'bg-emerald-500/10', textColor: 'text-emerald-400', borderColor: 'border-emerald-500/20' },
  { bgColor: 'bg-amber-500/10', textColor: 'text-amber-400', borderColor: 'border-amber-500/20' },
  { bgColor: 'bg-rose-500/10', textColor: 'text-rose-400', borderColor: 'border-rose-500/20' },
  { bgColor: 'bg-violet-500/10', textColor: 'text-violet-400', borderColor: 'border-violet-500/20' },
  { bgColor: 'bg-cyan-500/10', textColor: 'text-cyan-400', borderColor: 'border-cyan-500/20' },
  { bgColor: 'bg-pink-500/10', textColor: 'text-pink-400', borderColor: 'border-pink-500/20' },
  { bgColor: 'bg-orange-500/10', textColor: 'text-orange-400', borderColor: 'border-orange-500/20' },
]

export default function Home() {
  const router = useRouter()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const { sheets, loading, refresh } = useSheets()

  function handleDatabaseCreated(tableName: string, displayName: string) {
    setShowCreateModal(false)
    refresh() // Re-fetch tables from Supabase so the new one appears
  }

  return (
    <>
      <AppHeader />
      <div className="flex h-[calc(100vh-64px)]">
        <AppSidebar />
        <main className="flex-1 min-w-0 p-6 md:p-10 lg:p-12 max-w-7xl mx-auto overflow-y-auto">
      <header className="mb-12">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Database Selection</h1>
            <p className="text-slate-400">Manage your Supabase data management tables and connected agents.</p>
          </div>
          <div className="flex items-center space-x-3">
            <button className="flex items-center space-x-2 bg-white/5 px-4 py-2 border border-white/5 rounded-lg text-sm font-medium hover:bg-white/10 transition-all text-white">
              <Filter size={16} />
              <span>Filter</span>
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center space-x-2 bg-primary text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-blue-600 transition-all shadow-lg shadow-primary/20"
            >
              <Plus size={16} />
              <span>New Database</span>
            </button>
          </div>
        </div>
      </header>

      <section>
        <div className="flex items-center justify-between mb-8">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-[0.2em]">All Databases</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading ? (
            <div className="col-span-full flex items-center justify-center py-20">
              <div className="text-center">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent mb-3"></div>
                <p className="text-muted-foreground">Loading databases...</p>
              </div>
            </div>
          ) : (
          sheets.map((sheet, idx) => {
            const colorConfig = CARD_COLORS[idx % CARD_COLORS.length]

            return (
              <Link
                key={sheet.id}
                href={`/${sheet.id}/${sheet.tabs[0].name}`}
                className="group relative bg-white/[0.03] border border-white/10 rounded-2xl p-6 backdrop-blur-xl hover:bg-white/[0.06] hover:border-white/20 transition-all duration-300 cursor-pointer"
              >
                <div className="flex items-start justify-between mb-6">
                  <div className={`h-12 w-12 ${colorConfig.bgColor} rounded-xl flex items-center justify-center ${colorConfig.textColor} group-hover:scale-105 transition-transform border ${colorConfig.borderColor}`}>
                    <Database size={24} />
                  </div>
                  <button className="text-slate-600 hover:text-slate-400 transition-colors">
                    <MoreHorizontal size={20} />
                  </button>
                </div>

                <h4 className="text-lg font-bold text-white mb-1">{sheet.name}</h4>
                <p className="text-sm text-slate-400 mb-6 font-medium">{sheet.tabs.length} {sheet.tabs.length === 1 ? 'table' : 'tables'}</p>

                <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold tracking-wider">
                    Active
                  </span>
                  <div className={`w-2 h-2 rounded-full ${colorConfig.bgColor.replace('/10', '/60')}`}></div>
                </div>
              </Link>
            )
          })
          )}

          <button
            onClick={() => setShowCreateModal(true)}
            className="group relative bg-white/[0.01] border-2 border-dashed border-white/10 rounded-2xl p-6 flex flex-col items-center justify-center text-center hover:bg-white/[0.03] hover:border-primary/40 transition-all duration-300 cursor-pointer"
          >
            <div className="h-12 w-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-slate-500 group-hover:text-primary transition-colors mb-4">
              <Plus size={24} />
            </div>
            <p className="text-sm font-semibold text-white">Create new database</p>
            <p className="text-[11px] text-slate-500 mt-1">Connect Supabase or start blank</p>
          </button>
        </div>
      </section>
        </main>
      </div>

      <CreateDatabaseModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreated={handleDatabaseCreated}
      />
    </>
  );
}
