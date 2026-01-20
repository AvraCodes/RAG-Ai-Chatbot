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
      <div className="mb-8 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 to-sky-600 shadow-xl pulse-glow">
        <Sparkles className="h-9 w-9 text-white" />
      </div>

      <h2 className="mb-3 text-3xl font-bold text-foreground text-balance text-center tracking-tight">
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
            className="h-auto justify-start whitespace-normal p-4 text-left text-sm font-normal glass-effect glass-border hover:scale-[1.02] transition-all duration-200 hover:shadow-lg bg-transparent"
            onClick={() => onExampleClick(question)}
          >
            {question}
          </Button>
        ))}
      </div>
    </div>
  )
}
