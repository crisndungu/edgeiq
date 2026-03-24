import { createClient, SupabaseClient } from '@supabase/supabase-js'

function getSupabaseClient(): SupabaseClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  if (!url || url.startsWith('your_') || !key || key.startsWith('your_')) {
    throw new Error('Supabase env vars not configured. Add real values to .env.local')
  }
  return createClient(url, key)
}

// Lazy singleton — only instantiated when first called at runtime
let _client: SupabaseClient | null = null
export function getClient(): SupabaseClient {
  if (!_client) _client = getSupabaseClient()
  return _client
}

// Alias for convenience in query files
export const supabase = new Proxy({} as SupabaseClient, {
  get(_, prop) {
    return (getClient() as unknown as Record<string | symbol, unknown>)[prop]
  },
})

// Server-side client with elevated privileges (API routes only)
export function createServiceClient(): SupabaseClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!
  return createClient(url, serviceKey)
}
