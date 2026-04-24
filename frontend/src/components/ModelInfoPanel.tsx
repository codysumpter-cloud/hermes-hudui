import { useApi } from '../hooks/useApi'
import Panel from './Panel'
import { formatTokens } from '../lib/utils'
import { useTranslation } from '../i18n'

interface ModelInfo {
  model: string
  provider: string
  family: string
  supports_tools: boolean
  supports_vision: boolean
  supports_reasoning: boolean
  supports_structured_output: boolean
  max_output_tokens: number
  auto_context_length: number
  config_context_length: number
  effective_context_length: number
  cost_input_per_m: number | null
  cost_output_per_m: number | null
  cost_cache_read_per_m: number | null
  release_date: string
  knowledge_cutoff: string
  found: boolean
}

function CapBadge({ active, label }: { active: boolean; label: string }) {
  return (
    <span
      className="px-2 py-1 text-[11px] rounded"
      style={{
        background: active ? 'var(--hud-primary)' : 'var(--hud-panel-alt, transparent)',
        color: active ? 'var(--hud-bg)' : 'var(--hud-text-dim)',
        border: active ? 'none' : '1px solid var(--hud-border)',
        opacity: active ? 1 : 0.6,
      }}
    >
      {active ? '✓ ' : '○ '}
      {label}
    </span>
  )
}

export default function ModelInfoPanel() {
  const { t } = useTranslation()
  const { data, isLoading } = useApi<ModelInfo>('/model-info', 30000)

  if (isLoading && !data) {
    return (
      <Panel title={t('modelInfo.title')} className="col-span-full">
        <div className="glow text-[13px] animate-pulse">{t('modelInfo.loading')}</div>
      </Panel>
    )
  }

  if (!data || !data.model) {
    return (
      <Panel title={t('modelInfo.title')} className="col-span-full">
        <div className="text-[13px]" style={{ color: 'var(--hud-text-dim)' }}>
          {t('modelInfo.none')}
        </div>
      </Panel>
    )
  }

  const costRow = (label: string, value: number | null) =>
    value !== null ? (
      <div className="flex justify-between py-0.5 text-[13px]">
        <span style={{ color: 'var(--hud-text-dim)' }}>{label}</span>
        <span>${value.toFixed(2)} / 1M</span>
      </div>
    ) : null

  return (
    <>
      <Panel title={t('modelInfo.identity')}>
        <div className="space-y-1 text-[13px]">
          <div className="flex justify-between">
            <span style={{ color: 'var(--hud-text-dim)' }}>{t('modelInfo.model')}</span>
            <span style={{ color: 'var(--hud-primary)' }} className="font-mono">{data.model}</span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: 'var(--hud-text-dim)' }}>{t('modelInfo.provider')}</span>
            <span>{data.provider || '—'}</span>
          </div>
          {data.family && (
            <div className="flex justify-between">
              <span style={{ color: 'var(--hud-text-dim)' }}>{t('modelInfo.family')}</span>
              <span>{data.family}</span>
            </div>
          )}
          {data.release_date && (
            <div className="flex justify-between">
              <span style={{ color: 'var(--hud-text-dim)' }}>{t('modelInfo.release')}</span>
              <span>{data.release_date}</span>
            </div>
          )}
          {data.knowledge_cutoff && (
            <div className="flex justify-between">
              <span style={{ color: 'var(--hud-text-dim)' }}>{t('modelInfo.knowledge')}</span>
              <span>{data.knowledge_cutoff}</span>
            </div>
          )}
        </div>

        <div className="mt-4">
          <div className="text-[12px] mb-2" style={{ color: 'var(--hud-text-dim)' }}>
            {t('modelInfo.capabilities')}
          </div>
          <div className="flex flex-wrap gap-2">
            <CapBadge active={data.supports_tools} label={t('modelInfo.tools')} />
            <CapBadge active={data.supports_vision} label={t('modelInfo.vision')} />
            <CapBadge active={data.supports_reasoning} label={t('modelInfo.reasoning')} />
            <CapBadge active={data.supports_structured_output} label={t('modelInfo.structured')} />
          </div>
          {!data.found && (
            <div className="mt-3 text-[11px]" style={{ color: 'var(--hud-text-dim)' }}>
              {t('modelInfo.notFound')}
            </div>
          )}
        </div>
      </Panel>

      <Panel title={t('modelInfo.limits')}>
        <div className="text-[13px] space-y-1">
          <div className="flex justify-between">
            <span style={{ color: 'var(--hud-text-dim)' }}>{t('modelInfo.effectiveContext')}</span>
            <span style={{ color: 'var(--hud-primary)' }}>{formatTokens(data.effective_context_length)}</span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: 'var(--hud-text-dim)' }}>{t('modelInfo.autoContext')}</span>
            <span>{formatTokens(data.auto_context_length)}</span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: 'var(--hud-text-dim)' }}>{t('modelInfo.configContext')}</span>
            <span>{data.config_context_length > 0 ? formatTokens(data.config_context_length) : t('modelInfo.unset')}</span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: 'var(--hud-text-dim)' }}>{t('modelInfo.maxOutput')}</span>
            <span>{formatTokens(data.max_output_tokens)}</span>
          </div>
        </div>

        {(data.cost_input_per_m !== null || data.cost_output_per_m !== null) && (
          <div className="mt-4 pt-3" style={{ borderTop: '1px solid var(--hud-border)' }}>
            <div className="text-[12px] mb-1" style={{ color: 'var(--hud-text-dim)' }}>
              {t('modelInfo.cost')}
            </div>
            {costRow(t('modelInfo.costInput'), data.cost_input_per_m)}
            {costRow(t('modelInfo.costOutput'), data.cost_output_per_m)}
            {costRow(t('modelInfo.costCacheRead'), data.cost_cache_read_per_m)}
          </div>
        )}
      </Panel>
    </>
  )
}
