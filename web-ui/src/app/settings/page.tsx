import { AppHeader } from '@/components/app-header'
import { AppSidebar } from '@/components/app-sidebar'

export default function SettingsPage() {
  return (
    <>
      <AppHeader />
      <div className="flex h-[calc(100vh-64px)]">
        <AppSidebar />
        <main className="flex-1 min-w-0 p-6 md:p-10 lg:p-12 max-w-4xl overflow-y-auto">
          <h1 className="text-2xl font-bold text-white mb-8">Settings</h1>

          <section className="mb-10">
            <h2 className="text-lg font-semibold text-white mb-4">Keyboard Shortcuts</h2>
            <div className="bg-white/[0.03] border border-white/10 rounded-xl overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left px-5 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Shortcut</th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  <tr>
                    <td className="px-5 py-3">
                      <kbd className="px-2.5 py-1 bg-white/5 border border-white/10 rounded-md font-mono text-xs text-white">Ctrl + A</kbd>
                    </td>
                    <td className="px-5 py-3 text-sm text-slate-300">Select all rows in the current table</td>
                  </tr>
                  <tr>
                    <td className="px-5 py-3">
                      <kbd className="px-2.5 py-1 bg-white/5 border border-white/10 rounded-md font-mono text-xs text-white">Ctrl + E</kbd>
                    </td>
                    <td className="px-5 py-3 text-sm text-slate-300">Export current table as CSV</td>
                  </tr>
                  <tr>
                    <td className="px-5 py-3">
                      <kbd className="px-2.5 py-1 bg-white/5 border border-white/10 rounded-md font-mono text-xs text-white">Ctrl + K</kbd>
                    </td>
                    <td className="px-5 py-3 text-sm text-slate-300">Focus the global search bar</td>
                  </tr>
                  <tr>
                    <td className="px-5 py-3">
                      <kbd className="px-2.5 py-1 bg-white/5 border border-white/10 rounded-md font-mono text-xs text-white">Delete</kbd>
                    </td>
                    <td className="px-5 py-3 text-sm text-slate-300">Delete selected rows</td>
                  </tr>
                  <tr>
                    <td className="px-5 py-3">
                      <kbd className="px-2.5 py-1 bg-white/5 border border-white/10 rounded-md font-mono text-xs text-white">Escape</kbd>
                    </td>
                    <td className="px-5 py-3 text-sm text-slate-300">Cancel selection or editing</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section className="mb-10">
            <h2 className="text-lg font-semibold text-white mb-4">About</h2>
            <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
              <p className="text-sm text-slate-400">
                AgentLink Database Management — An Airtable-like interface for managing Supabase data tables.
              </p>
            </div>
          </section>
        </main>
      </div>
    </>
  )
}
