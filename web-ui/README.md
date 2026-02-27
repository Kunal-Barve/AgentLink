# AgentLink Database Management UI

**Airtable-like interface for managing AgentLink Supabase data**

## ⚠️ Critical: Isolation from FastAPI

This web UI is **completely separate** from the FastAPI PDF generation service:
- ✅ Different directory (`/web-ui` vs `/app`)
- ✅ Different runtime (Node.js vs Python)
- ✅ Different dependencies (package.json vs requirements.txt)
- ✅ **FastAPI PDF endpoints are NOT affected**

## Features

- 📊 **Sheet-based navigation** (like Google Sheets)
- 🏷️ **Tab management** (multiple tabs per sheet)
- 📝 **CRUD operations** (add, edit, delete rows)
- 🔄 **Real-time data** (from Supabase)
- 🎨 **Airtable-like UI** (clean, modern interface)

## Setup

### 1. Environment Variables

Edit `.env.local`:
```bash
NEXT_PUBLIC_SUPABASE_URL=http://srv1165267.hstgr.cloud:8000
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_actual_anon_key
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Project Structure

```
web-ui/
├── src/
│   ├── app/                # Next.js pages
│   │   ├── [sheet]/       # Dynamic sheet routes
│   │   │   └── [tab]/     # Dynamic tab routes
│   │   └── page.tsx       # Home (sheet selector)
│   ├── components/         # React components
│   │   ├── ui/            # Base UI components
│   │   ├── sheet-nav.tsx  # Sheet navigation sidebar
│   │   ├── tab-bar.tsx    # Tab switcher
│   │   └── data-grid.tsx  # Airtable-like data table
│   └── lib/
│       ├── supabase.ts    # Supabase client
│       └── sheet-config.ts # Sheet → Tab → Table mapping
```

## Sheet Configuration

All sheet/tab/table mappings are in `src/lib/sheet-config.ts`:

```typescript
{
  id: 'featured-agent-controls',
  name: 'Featured Agent Controls',
  tabs: [
    { name: 'sheet1', tableName: 'featured_agent_controls' },
    { name: 'sheet3', tableName: 'featured_agent_controls_sheet3' }
  ]
}
```

## Development

- **Port**: 3000 (default Next.js)
- **FastAPI Port**: 8000 (runs independently)
- **Supabase**: srv1165267.hstgr.cloud:8000

## Deployment

This UI can be deployed separately:
- **Vercel**: Recommended for Next.js
- **Docker**: Can be containerized independently
- **Static export**: `npm run build && npm run export`

## FastAPI Status ✅

The FastAPI service in `/app` directory is **completely untouched**:
- PDF generation endpoints: Working
- Domain.au integration: Working
- All existing functionality: Preserved
