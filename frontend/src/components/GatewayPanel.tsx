import { useCallback, useEffect, useRef, useState } from 'react'
import { useApi } from '../hooks/useApi'
import Panel from './Panel'
import { timeAgo } from '../lib/utils'
import { useTranslation } from '../i18n'
import { mutate } from 'swr'

interface GatewayData {
  state: string
  pid: number | null
  pid_alive: boolean
  kind: string
  restart_requested: boolean
  exit_reason: string | null
  updated_at: string | null
  active_agents: number
  platforms: {
    name: string
    state: string
    updated_at: string | null
    error_code: string | null
    error_message: string | null
  }[]
}

interface ActionStatus {
  name: string
  pid: number | null
  running: boolean
  exit_code: number | null
  started_at: number | null
  log_path: string
  lines: string[]
}

function platformColor(state: string): string {
  if (state === 'connected' || state === 'running') return 'var(--hud-success)'
  if (state === 'connecting' || state === 'starting') return 'var(--hud-warning, #d4a017)'
  return 'var(--hud-error)'
}

function ActionRunner({
  actionName,
  postPath,
  label,
  onStateChange,
}: {
  actionName: string
  postPath: string
  label: string
  onStateChange: () => void
}) {
  const { t } = useTranslation()
  const [polling, setPolling] = useState(false)
  const [status, setStatus] = useState<ActionStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<number | null>(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current)
        timerRef.current = null
      }
    }
  }, [])

  const pollOnce = useCallback(async () => {
    try {
      const res = await fetch(`/api/actions/${actionName}/status`)
      if (!res.ok) throw new Error(`${res.status}`)
      const data: ActionStatus = await res.json()
      if (!mountedRef.current) return
      setStatus(data)
      if (data.running) {
        timerRef.current = window.setTimeout(pollOnce, 1000)
      } else {
        setPolling(false)
        onStateChange()
      }
    } catch (e: any) {
      if (!mountedRef.current) return
      setError(String(e.message || e))
      setPolling(false)
    }
  }, [actionName, onStateChange])

  const trigger = async () => {
    setError(null)
    setStatus(null)
    setPolling(true)
    try {
      const res = await fetch(postPath, { method: 'POST' })
      if (!res.ok) throw new Error(await res.text())
      if (!mountedRef.current) return
      timerRef.current = window.setTimeout(pollOnce, 500)
    } catch (e: any) {
      if (!mountedRef.current) return
      setError(String(e.message || e))
      setPolling(false)
    }
  }

  return (
    <div>
      <button
        onClick={trigger}
        disabled={polling}
        className="px-3 py-1.5 text-[13px] rounded"
        style={{
          background: polling ? 'var(--hud-panel-alt, transparent)' : 'var(--hud-primary)',
          color: polling ? 'var(--hud-text-dim)' : 'var(--hud-bg)',
          cursor: polling ? 'not-allowed' : 'pointer',
          border: '1px solid var(--hud-border)',
        }}
      >
        {polling ? t('gateway.running') : label}
      </button>
      {error && (
        <div className="mt-2 text-[12px]" style={{ color: 'var(--hud-error)' }}>
          {error}
        </div>
      )}
      {status && status.lines.length > 0 && (
        <pre
          className="mt-2 p-2 text-[11px] overflow-auto max-h-48 font-mono"
          style={{
            background: 'var(--hud-panel-alt, rgba(0,0,0,0.2))',
            border: '1px solid var(--hud-border)',
            color: 'var(--hud-text-dim)',
          }}
        >
          {status.lines.slice(-40).join('\n')}
        </pre>
      )}
      {status && !status.running && status.exit_code !== null && (
        <div className="mt-1 text-[11px]" style={{ color: status.exit_code === 0 ? 'var(--hud-success)' : 'var(--hud-error)' }}>
          {t('gateway.exitCode')}: {status.exit_code}
        </div>
      )}
    </div>
  )
}

export default function GatewayPanel() {
  const { t } = useTranslation()
  const { data, isLoading } = useApi<GatewayData>('/gateway', 10000)

  const refresh = useCallback(() => {
    mutate('/api/gateway')
  }, [])

  if (isLoading && !data) {
    return (
      <Panel title={t('gateway.title')} className="col-span-full">
        <div className="glow text-[13px] animate-pulse">{t('gateway.loading')}</div>
      </Panel>
    )
  }

  const healthy = data?.state === 'running' && data?.pid_alive

  return (
    <Panel title={t('gateway.title')} className="col-span-full">
      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <div className="text-[13px] space-y-1">
            <div className="flex justify-between">
              <span style={{ color: 'var(--hud-text-dim)' }}>{t('gateway.state')}</span>
              <span style={{ color: healthy ? 'var(--hud-success)' : 'var(--hud-error)' }}>
                ● {data?.state ?? 'unknown'}
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: 'var(--hud-text-dim)' }}>{t('gateway.pid')}</span>
              <span>{data?.pid ?? '—'}{data && !data.pid_alive && data.pid ? ` (${t('gateway.dead')})` : ''}</span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: 'var(--hud-text-dim)' }}>{t('gateway.activeAgents')}</span>
              <span>{data?.active_agents ?? 0}</span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: 'var(--hud-text-dim)' }}>{t('gateway.updated')}</span>
              <span>{timeAgo(data?.updated_at)}</span>
            </div>
            {data?.exit_reason && (
              <div className="flex justify-between">
                <span style={{ color: 'var(--hud-text-dim)' }}>{t('gateway.exitReason')}</span>
                <span style={{ color: 'var(--hud-error)' }}>{data.exit_reason}</span>
              </div>
            )}
          </div>

          <div className="mt-4">
            <div className="text-[12px] mb-1" style={{ color: 'var(--hud-text-dim)' }}>
              {t('gateway.platforms')}
            </div>
            {(data?.platforms ?? []).length === 0 && (
              <div className="text-[13px]" style={{ color: 'var(--hud-text-dim)' }}>—</div>
            )}
            {(data?.platforms ?? []).map((p) => (
              <div key={p.name} className="flex justify-between text-[13px] py-0.5">
                <span>{p.name}</span>
                <span style={{ color: platformColor(p.state) }}>● {p.state}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <div className="text-[12px] mb-2" style={{ color: 'var(--hud-text-dim)' }}>
              {t('gateway.actions')}
            </div>
            <div className="space-y-3">
              <ActionRunner
                actionName="gateway-restart"
                postPath="/api/gateway/restart"
                label={t('gateway.restart')}
                onStateChange={refresh}
              />
              <ActionRunner
                actionName="hermes-update"
                postPath="/api/hermes/update"
                label={t('gateway.update')}
                onStateChange={refresh}
              />
            </div>
          </div>
        </div>
      </div>
    </Panel>
  )
}
