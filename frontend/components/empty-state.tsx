'use client';

import { Button } from './ui/button'
import { Sparkles } from 'lucide-react'

interface EmptyStateProps {
  onExampleClick: (question: string) => void
}

const exampleQuestions = [
  'What is Principal Component Analysis?',
  'How does FastAPI handle async requests?',
  'Explain the concept of transfer learning',
  'What are the benefits of using TypeScript?',
]

export function EmptyState({ onExampleClick }: EmptyStateProps) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center animate-in fade-in duration-500">
      <div className="mb-8 relative">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-full blur-2xl opacity-40 animate-pulse"></div>
        <div className="relative flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 shadow-2xl pulse-glow">
          <Sparkles className="h-11 w-11 text-white" />
        </div>
      </div>

      <h2 className="mb-3 text-4xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent text-balance text-center tracking-tight">
        Ask me anything
      </h2>
      <p className="mb-10 text-center text-muted-foreground/80 text-pretty max-w-md text-[15px] leading-relaxed">
        {'I can answer questions using retrieved documents. Get started with an example below.'}
      </p>

      <div className="grid w-full max-w-2xl grid-cols-1 gap-3 md:grid-cols-2">
        {exampleQuestions.map((question, index) => (
          <Button
            key={index}
            variant="outline"
            className="h-auto justify-start whitespace-normal p-4 text-left text-sm font-normal glass-effect glass-border hover:scale-[1.03] transition-all duration-300 hover:shadow-xl hover:shadow-purple-500/20 bg-transparent group relative overflow-hidden"
            onClick={() => onExampleClick(question)}
          >
            {question}
          </Button>
        ))}
      </div>
    </div>
  )
}
