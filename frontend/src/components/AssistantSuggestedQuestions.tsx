import "./AssistantSuggestedQuestions.css"

type AssistantSuggestedQuestionsProps = {
  disabled: boolean
  onSelect: (question: string) => void
}

const SUGGESTED_QUESTIONS = [
  "What's our bookkeeping summary?",
  "Show me Microsoft transactions.",
  "Which transactions need AI review?",
  "Show me reconciliation review.",
  "Which transactions look unusual?",
  "What's our largest expense?",
]

export function AssistantSuggestedQuestions({
  disabled,
  onSelect,
}: AssistantSuggestedQuestionsProps) {
  return (
    <div
      className="assistant-suggestions"
      aria-label="Suggested Assistant questions"
    >
      <span className="assistant-suggestions-label">
        Suggested questions
      </span>

      <div className="assistant-suggestion-list">
        {SUGGESTED_QUESTIONS.map((question) => (
          <button
            key={question}
            type="button"
            className="assistant-suggestion-button"
            onClick={() => onSelect(question)}
            disabled={disabled}
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}
