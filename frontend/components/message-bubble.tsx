'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink, User, Sparkles } from 'lucide-react'
import { Button } from './ui/button'
import type { Message } from '@/app/page'

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [isSourcesExpanded, setIsSourcesExpanded] = useState(false)

  return (
    <div
      className={`flex gap-4 message-enter ${
        message.role === 'user' ? 'justify-end' : 'justify-start'
      }`}
    >
      {message.role === 'assistant' && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white shadow-lg glow-green relative">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-full blur-md opacity-50 animate-pulse"></div>
          <Sparkles className="h-4 w-4 relative z-10" />
        </div>
      )}

      <div className="flex max-w-[85%] flex-col gap-2">
        {message.role === 'user' && message.image && (
          <div className="overflow-hidden rounded-xl border border-border/50 shadow-md">
            <img
              src={message.image || "/placeholder.svg"}
              alt="User uploaded"
              className="max-h-64 w-auto object-contain"
            />
          </div>
        )}

        <div
          className={`rounded-2xl px-5 py-3.5 shadow-md transition-all duration-200 ${
            message.role === 'user'
              ? 'bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white shadow-lg shadow-purple-500/30'
              : 'glass-effect glass-border text-foreground'
          }`}
        >
          <p className={`whitespace-pre-wrap leading-relaxed ${message.role === 'user' ? 'text-sm' : 'text-[15px]'}`}>
            {message.content}
          </p>
        </div>

        {message.role === 'assistant' && message.links && message.links.length > 0 && (
          <div className="mt-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsSourcesExpanded(!isSourcesExpanded)}
              className="h-auto gap-2 px-2 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors duration-200 rounded-lg hover:bg-accent/50"
            >
              <span className="font-medium">
                {message.links.length} {message.links.length === 1 ? 'Source' : 'Sources'}
              </span>
              {isSourcesExpanded ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </Button>

            {isSourcesExpanded && (
              <div className="mt-2 space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
                <p className="text-xs font-medium text-muted-foreground mb-2">Sources used for this answer:</p>
                {message.links.map((link, index) => (
                  <a
                    key={index}
                    href={link.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group flex items-start gap-3 rounded-xl glass-effect glass-border p-3.5 transition-all duration-200 hover:scale-[1.02] hover:shadow-lg"
                  >
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 text-white shadow-md">
                      <ExternalLink className="h-3.5 w-3.5" />
                    </div>
                    <div className="flex-1 overflow-hidden">
                      <p className="text-xs text-foreground/90 line-clamp-2 leading-relaxed">
                        {link.text}
                      </p>
                      <p className="mt-1.5 truncate text-[11px] text-muted-foreground">
                        {link.url}
                      </p>
                    </div>
                  </a>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {message.role === 'user' && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full glass-effect glass-border text-foreground shadow-md">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  )
}
