'use client'

import React from "react"

import { useState, useRef, KeyboardEvent } from 'react'
import { Button } from './ui/button'
import { Textarea } from './ui/textarea'
import { ArrowUp, ImageIcon, X } from 'lucide-react'

interface ChatInputProps {
  onSendMessage: (message: string, image?: string) => void
  isLoading: boolean
  disabled: boolean
}

export function ChatInput({ onSendMessage, isLoading, disabled }: ChatInputProps) {
  const [input, setInput] = useState('')
  const [image, setImage] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSendMessage(input, image || undefined)
      setInput('')
      setImage(null)
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setImage(reader.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const removeImage = () => {
    setImage(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="border-t border-border/30 glass-effect">
      <div className="mx-auto max-w-3xl px-4 py-4">
        {image && (
          <div className="mb-3 relative inline-block animate-in fade-in slide-in-from-bottom-2 duration-200">
            <img
              src={image || "/placeholder.svg"}
              alt="Upload preview"
              className="max-h-32 rounded-xl border border-border/50 shadow-lg"
            />
            <Button
              variant="destructive"
              size="icon"
              className="absolute -right-2 -top-2 h-6 w-6 rounded-full shadow-md hover:scale-110 transition-transform duration-200"
              onClick={removeImage}
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        )}

        <div className="flex items-end gap-3">
          <div className="relative flex-1">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question..."
              disabled={disabled}
              className="min-h-[56px] max-h-[200px] resize-none rounded-2xl glass-effect glass-border pr-12 text-sm focus-visible:ring-2 focus-visible:ring-purple-500/50 focus-visible:border-purple-500/50 focus-visible:glow-effect transition-all duration-200 text-foreground placeholder:text-muted-foreground/70"
              rows={1}
            />
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              className="hidden"
            />
            <Button
              variant="ghost"
              size="icon"
              className="absolute bottom-2 right-2 h-8 w-8 text-muted-foreground hover:text-foreground hover:scale-110 transition-all duration-200"
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled}
            >
              <ImageIcon className="h-4 w-4" />
            </Button>
          </div>

          <Button
            onClick={handleSubmit}
            disabled={!input.trim() || disabled}
            size="icon"
            className="h-[56px] w-[56px] shrink-0 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 hover:from-indigo-400 hover:via-purple-400 hover:to-pink-400 shadow-lg shadow-purple-500/50 hover:shadow-purple-500/70 hover:scale-105 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 relative overflow-hidden group"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>
            {isLoading ? (
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent relative z-10" />
            ) : (
              <ArrowUp className="h-5 w-5 relative z-10" />
            )}
          </Button>
        </div>

        <p className="mt-2.5 text-center text-xs text-muted-foreground/70">
          Press Enter to send, Shift + Enter for new line
        </p>
      </div>
    </div>
  )
}
