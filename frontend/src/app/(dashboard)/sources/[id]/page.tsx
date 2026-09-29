'use client'

import { useRouter, useParams } from 'next/navigation'
import { useCallback, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ArrowLeft, FileText, MessageSquare } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useTranslation } from '@/lib/hooks/use-translation'
import { useSourceChat } from '@/lib/hooks/use-source-chat'
import { ChatPanel } from '@/components/sources/ChatPanel'
import { useNavigation } from '@/lib/hooks/use-navigation'
import { SourceDetailContent } from '@/components/sources/SourceDetailContent'

export default function SourceDetailPage() {
  const router = useRouter()
  const params = useParams()
  const sourceId = params?.id ? decodeURIComponent(params.id as string) : ''
  const navigation = useNavigation()
  const { t } = useTranslation()
  // Below lg the two columns don't fit side by side; show one at a time.
  const [mobileTab, setMobileTab] = useState<'content' | 'chat'>('content')

  // Initialize source chat
  const chat = useSourceChat(sourceId)

  const handleBack = useCallback(() => {
    const returnPath = navigation.getReturnPath()
    router.push(returnPath)
    navigation.clearReturnTo()
  }, [navigation, router])

  return (
    <div className="flex flex-col h-dvh pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)]">
      {/* Back button */}
      <div className="pt-3 pb-2 px-2 sm:pt-6 sm:pb-4 sm:px-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleBack}
          className="lg:mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          {navigation.getReturnLabel()}
        </Button>
      </div>

      <div className="px-4 pb-3 lg:hidden">
        <Tabs value={mobileTab} onValueChange={(value) => setMobileTab(value as 'content' | 'chat')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="content" className="gap-2">
              <FileText className="h-4 w-4" />
              {t('sources.content')}
            </TabsTrigger>
            <TabsTrigger value="chat" className="gap-2">
              <MessageSquare className="h-4 w-4" />
              {t('common.chat')}
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Main content: Source detail + Chat */}
      <div className="flex-1 min-h-0 grid grid-rows-[minmax(0,1fr)] gap-6 lg:grid-cols-[2fr_1fr] overflow-hidden px-0 lg:px-6">
        {/* Left column - Source detail */}
        <div className={cn('min-h-0 overflow-y-auto px-4 pb-6', mobileTab !== 'content' && 'hidden lg:block')}>
          <SourceDetailContent
            sourceId={sourceId}
            showChatButton={false}
            onClose={handleBack}
          />
        </div>

        {/* Right column - Chat */}
        <div className={cn('min-h-0 overflow-y-auto px-4 pb-4 lg:pb-6', mobileTab !== 'chat' && 'hidden lg:block')}>
          <ChatPanel
            messages={chat.messages}
            isStreaming={chat.isStreaming}
            contextIndicators={chat.contextIndicators}
            onSendMessage={(message, model) => chat.sendMessage(message, model)}
            modelOverride={chat.currentSession?.model_override}
            onModelChange={(model) => {
              if (chat.currentSessionId) {
                chat.updateSession(chat.currentSessionId, { model_override: model })
              }
            }}
            sessions={chat.sessions}
            currentSessionId={chat.currentSessionId}
            onCreateSession={(title) => chat.createSession({ title })}
            onSelectSession={chat.switchSession}
            onUpdateSession={(sessionId, title) => chat.updateSession(sessionId, { title })}
            onDeleteSession={chat.deleteSession}
            loadingSessions={chat.loadingSessions}
          />
        </div>
      </div>
    </div>
  )
}
