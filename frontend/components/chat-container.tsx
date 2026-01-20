import { MessageBubble } from './message-bubble'
import { LoadingIndicator } from './loading-indicator'
import type { Message } from '@/app/page'

interface ChatContainerProps {
  messages: Message[]
  isLoading: boolean
}

export function ChatContainer({ messages, isLoading }: ChatContainerProps) {
  return (
    <div className="space-y-6">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {isLoading && <LoadingIndicator />}
    </div>
  )
}
