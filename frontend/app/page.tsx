'use client'

import { useState, useRef, useEffect } from 'react'
import { ChatContainer } from '@/components/chat-container'
import { ChatInput } from '@/components/chat-input'
import { EmptyState } from '@/components/empty-state'
import { Button } from '@/components/ui/button'
import { Trash2 } from 'lucide-react'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  links?: { url: string; text: string }[]
  image?: string
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (question: string, image?: string) => {
    if (!question.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      image,
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/api', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          ...(image && { image }),
        }),
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Server error: ${response.status} - ${errorText}`)
      }

      const data = await response.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        links: data.links,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      console.error('[v0] Error sending message:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearChat = () => {
    setMessages([])
    setError(null)
  }

  const handleRetry = () => {
    if (messages.length > 0) {
      const lastUserMessage = [...messages]
        .reverse()
        .find((m) => m.role === 'user')
      if (lastUserMessage) {
        handleSendMessage(lastUserMessage.content, lastUserMessage.image)
      }
    }
  }

  return (
    <div className="flex h-screen flex-col bg-gradient-dark relative overflow-hidden">
      {/* Animated ambient glow effects */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-sky-400 opacity-15 rounded-full blur-3xl pointer-events-none float-animation" />
      <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-sky-500 opacity-20 rounded-full blur-3xl pointer-events-none float-animation-delayed" />
      <div className="absolute top-1/2 right-1/3 w-[300px] h-[300px] bg-sky-300 opacity-10 rounded-full blur-3xl pointer-events-none float-animation" style={{ animationDelay: '4s' }} />
      <div className="absolute bottom-0 left-1/3 w-[350px] h-[350px] bg-sky-600 opacity-10 rounded-full blur-3xl pointer-events-none float-animation-delayed" style={{ animationDelay: '1s' }} />
      
      {/* Header */}
      <header className="flex h-14 items-center justify-between border-b border-border/30 px-4 glass-effect relative z-10">
        <h1 className="text-sm font-semibold text-foreground tracking-tight">
          RAG AI Assistant
        </h1>
        {messages.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearChat}
            className="text-muted-foreground hover:text-foreground transition-all duration-200 hover:scale-105"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </header>

      {/* Chat Container */}
      <div className="flex-1 overflow-y-auto relative z-10">
        <div className="mx-auto max-w-3xl px-4 py-8">
          {messages.length === 0 ? (
            <EmptyState onExampleClick={handleSendMessage} />
          ) : (
            <>
              <ChatContainer messages={messages} isLoading={isLoading} />
              <div ref={messagesEndRef} />
            </>
          )}

          {error && (
            <div className="mt-4 rounded-xl glass-effect glass-border p-4 glow-effect">
              <p className="text-sm text-destructive">{error}</p>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetry}
                className="mt-2 bg-transparent hover:scale-105 transition-transform duration-200"
              >
                Retry
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="relative z-10">
        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          disabled={isLoading}
        />
      </div>
    </div>
  )
}
