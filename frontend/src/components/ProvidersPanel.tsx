import { useApi } from '../hooks/useApi'
import Panel from './Panel'
import { timeAgo } from '../lib/utils'
import { useTranslation } from '../i18n'

type Status = 'connected' | 'expiring' | 'expired' | 'missing'

interface Provider {
  id: string
  name: string
  status: Status
  token_preview: string
  expires_at: string | null
  obtained_at: string | null
  scope: string
  is_active: boolean
  auth_mode: string
}

const STATUS_COLOR: Record<Status, string> = {
  connected: 'var(--hud-success)',
  expiring: 'var(--hud-warning, #d4a017)',
  expired: 'var(--hud-error)',
  missing: 'var(--hud-text-dim)',
}

const STATUS_LABEL: Record<Status, string> = {
  connected: 'connected',
  expiring: 'expiring',
  expired: 'expired',
  missing: 'missing',
}

export default function ProvidersPanel() {
  const { t } = useTranslation()
  const { data, isLoading } = useApi<{ providers: Provider[]; active_provider: string | null }>('/providers', 30000)

  if (isLoading && !data) {
    return (
      <Panel title={t('providers.title')} className="col-span-full">
        <div className="glow text-[13px] animate-pulse">{t('providers.loading')}</div>
      </Panel>
    )
  }

  const providers: Provider[] = data?.providers ?? []

  return (
    <Panel title={t('providers.title')} className="col-span-full">
      <div className="text-[12px] mb-3" style={{ color: 'var(--hud-text-dim)' }}>
        {t('providers.subtitle')}
      </div>
      {providers.length === 0 && (
        <div className="text-[13px]" style={{ color: 'var(--hud-text-dim)' }}>
          {t('providers.none')}
        </div>
      )}
      <div className="space-y-2 text-[13px]">
        {providers.map((p) => {
          const when = p.expires_at
            ? `${t('providers.expires')} ${timeAgo(p.expires_at)}`
            : p.obtained_at
              ? `${t('providers.obtained')} ${timeAgo(p.obtained_at)}`
              : ''
          return (
          <div
            key={p.id}
            className="py-2 px-3"
            style={{
              borderLeft: `3px solid ${STATUS_COLOR[p.status]}`,
              background: p.is_active ? 'var(--hud-panel-alt, transparent)' : 'transparent',
            }}
          >
            <div className="flex justify-between items-baseline">
              <div className="flex items-baseline gap-2">
                <span className="font-medium">{p.name}</span>
                {p.is_active && (
                  <span
                    className="text-[10px] px-1.5 py-0.5 rounded"
                    style={{ background: 'var(--hud-primary)', color: 'var(--hud-bg)' }}
                  >
                    {t('providers.active')}
                  </span>
                )}
                {p.auth_mode && (
                  <span className="text-[10px]" style={{ color: 'var(--hud-text-dim)' }}>
                    {p.auth_mode}
                  </span>
                )}
              </div>
              <span style={{ color: STATUS_COLOR[p.status], fontVariant: 'small-caps' }}>
                ● {STATUS_LABEL[p.status]}
              </span>
            </div>
            <div className="mt-1 flex justify-between" style={{ color: 'var(--hud-text-dim)' }}>
              <span className="font-mono">{p.token_preview || '—'}</span>
              <span>{when}</span>
            </div>
            {p.scope && (
              <div className="mt-0.5 text-[11px]" style={{ color: 'var(--hud-text-dim)' }}>
                {t('providers.scope')}: {p.scope}
              </div>
            )}
          </div>
          )
        })}
      </div>
    </Panel>
  )
}
