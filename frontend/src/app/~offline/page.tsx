'use client'

import { useTranslation } from '@/lib/hooks/use-translation'

// Served by the service worker when a page can't be reached. Locales are
// bundled, so this renders without the API.
export default function OfflinePage() {
  const { t } = useTranslation()

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-3 p-6 text-center">
      <span className="flex items-center gap-[3px]" aria-hidden="true">
        <span className="size-[10px] rounded-[3px] bg-fern" />
        <span className="size-[10px] rounded-[3px] bg-gold" />
        <span className="size-[10px] rounded-[3px] bg-teal" />
      </span>
      <h1 className="font-display text-xl font-bold">{t('pwa.offlineTitle')}</h1>
      <p className="max-w-sm text-sm text-muted-foreground">{t('pwa.offlineDesc')}</p>
    </div>
  )
}
