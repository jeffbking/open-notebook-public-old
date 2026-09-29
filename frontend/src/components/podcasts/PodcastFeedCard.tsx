'use client'

import { Copy, Rss } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { usePodcastFeedInfo } from '@/lib/hooks/use-podcasts'
import { useTranslation } from '@/lib/hooks/use-translation'

/** Private RSS feed URL for podcast apps; hidden unless the server enables it. */
export function PodcastFeedCard() {
  const { t } = useTranslation()
  const { data } = usePodcastFeedInfo()

  if (!data?.enabled || !data.feed_url) {
    return null
  }
  const feedUrl = data.feed_url

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(feedUrl)
      toast.success(t('common.copyToClipboard'))
    } catch {
      toast.error(t('common.error'))
    }
  }

  return (
    <div className="space-y-3 rounded-lg border bg-card p-4">
      <div className="flex items-start gap-3">
        <Rss className="mt-0.5 h-4 w-4 flex-shrink-0 text-mauve" />
        <div className="space-y-1">
          <h3 className="text-sm font-semibold">{t('podcasts.feedTitle')}</h3>
          <p className="text-xs text-muted-foreground">{t('podcasts.feedDesc')}</p>
        </div>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <Input
          readOnly
          value={feedUrl}
          aria-label={t('podcasts.feedTitle')}
          onFocus={(event) => event.currentTarget.select()}
          className="min-w-0 flex-1 font-mono text-xs"
        />
        <Button variant="outline" onClick={handleCopy} className="flex-shrink-0">
          <Copy className="mr-2 h-4 w-4" />
          {t('podcasts.copyFeedUrl')}
        </Button>
      </div>
    </div>
  )
}
