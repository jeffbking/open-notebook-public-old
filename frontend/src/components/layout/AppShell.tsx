'use client'

import { useState } from 'react'
import { Menu } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'
import { useTranslation } from '@/lib/hooks/use-translation'
import { AppSidebar } from './AppSidebar'
import { SetupBanner } from './SetupBanner'

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const { t } = useTranslation()
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  return (
    <div className="flex h-dvh flex-col overflow-hidden md:flex-row">
      {/* Desktop / tablet: persistent sidebar */}
      <div className="hidden md:flex">
        <AppSidebar />
      </div>

      {/* Phone: top bar + slide-in drawer */}
      <header className="flex h-14 flex-shrink-0 items-center gap-2 border-b border-sidebar-border bg-sidebar px-2 pt-[env(safe-area-inset-top)] box-content md:hidden">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setMobileNavOpen(true)}
          aria-label={t('navigation.nav')}
          className="text-sidebar-foreground"
        >
          <Menu className="h-5 w-5" />
        </Button>
        <span className="flex items-center gap-[3px]" aria-hidden="true">
          <span className="size-[8px] rounded-[3px] bg-fern" />
          <span className="size-[8px] rounded-[3px] bg-gold" />
          <span className="size-[8px] rounded-[3px] bg-teal" />
        </span>
        <span className="font-display text-[15px] font-bold tracking-tight text-sidebar-foreground">
          {t('common.appName')}
        </span>
      </header>
      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent
          side="left"
          // Don't ring the first nav item on open; focus the drawer itself.
          onOpenAutoFocus={(event) => {
            event.preventDefault()
            ;(event.currentTarget as HTMLElement | null)?.focus()
          }}
          className="w-[82vw] max-w-72 gap-0 p-0 pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] bg-sidebar outline-none"
        >
          <SheetTitle className="sr-only">{t('common.appName')}</SheetTitle>
          <AppSidebar mobile onNavigate={() => setMobileNavOpen(false)} />
        </SheetContent>
      </Sheet>

      <main className="flex flex-1 flex-col min-h-0 min-w-0 overflow-hidden pb-[env(safe-area-inset-bottom)]">
        <SetupBanner />
        {children}
      </main>
    </div>
  )
}
