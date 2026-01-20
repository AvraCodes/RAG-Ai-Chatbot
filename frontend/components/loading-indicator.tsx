import { Sparkles } from 'lucide-react'

export function LoadingIndicator() {
  return (
    <div className="flex gap-4 message-enter">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-sky-600 text-white shadow-lg glow-green">
        <Sparkles className="h-4 w-4" />
      </div>

      <div className="flex max-w-[85%] items-center gap-2 rounded-2xl glass-effect glass-border px-5 py-3.5 shadow-md">
        <div className="flex gap-1.5">
          <div
            className="h-2 w-2 animate-bounce rounded-full bg-sky-500 glow-green"
            style={{ animationDelay: '0ms' }}
          />
          <div
            className="h-2 w-2 animate-bounce rounded-full bg-sky-500 glow-green"
            style={{ animationDelay: '150ms' }}
          />
          <div
            className="h-2 w-2 animate-bounce rounded-full bg-sky-500 glow-green"
            style={{ animationDelay: '300ms' }}
          />
        </div>
      </div>
    </div>
  )
}
