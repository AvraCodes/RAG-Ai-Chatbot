import { Sparkles } from 'lucide-react'

export function LoadingIndicator() {
  return (
    <div className="flex gap-4 message-enter">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white shadow-lg relative">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-full blur-md opacity-50 animate-pulse"></div>
        <Sparkles className="h-4 w-4 relative z-10 animate-pulse" />
      </div>

      <div className="flex max-w-[85%] items-center gap-2 rounded-2xl glass-effect glass-border px-5 py-3.5 shadow-md">
        <div className="flex gap-1.5">
          <div
            className="h-2 w-2 animate-bounce rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 shadow-sm shadow-purple-500/50"
            style={{ animationDelay: '0ms' }}
          />
          <div
            className="h-2 w-2 animate-bounce rounded-full bg-gradient-to-br from-purple-500 to-pink-500 shadow-sm shadow-pink-500/50"
            style={{ animationDelay: '150ms' }}
          />
          <div
            className="h-2 w-2 animate-bounce rounded-full bg-gradient-to-br from-pink-500 to-indigo-500 shadow-sm shadow-indigo-500/50"
            style={{ animationDelay: '300ms' }}
          />
        </div>
      </div>
    </div>
  )
}
