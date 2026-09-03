export type AssistantTransaction = {
  transaction_id: number
  transaction_date: string
  transaction_type: string
  description: string
  amount: number
  category: string | null
  vendor: string | null
  ai_suggested_category: string | null
  ai_confidence: number | null
  reconciliation_status: string
  status: string
}

type ToolExecution = {
  tool_name: string
  result: unknown
}

const TRANSACTION_TOOL_NAMES = new Set([
  "get_transactions",
  "get_transactions_by_date",
])

function isObject(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  )
}

function isNullableString(
  value: unknown,
): value is string | null {
  return value === null || typeof value === "string"
}

function isAssistantTransaction(
  value: unknown,
): value is AssistantTransaction {
  if (!isObject(value)) {
    return false
  }

  return (
    typeof value.transaction_id === "number" &&
    typeof value.transaction_date === "string" &&
    typeof value.transaction_type === "string" &&
    typeof value.description === "string" &&
    typeof value.amount === "number" &&
    isNullableString(value.category) &&
    isNullableString(value.vendor) &&
    isNullableString(value.ai_suggested_category) &&
    (
      value.ai_confidence === null ||
      typeof value.ai_confidence === "number"
    ) &&
    typeof value.reconciliation_status === "string" &&
    typeof value.status === "string"
  )
}

function isAssistantTransactionList(
  value: unknown,
): value is AssistantTransaction[] {
  return (
    Array.isArray(value) &&
    value.every(isAssistantTransaction)
  )
}

function isToolExecution(
  value: unknown,
): value is ToolExecution {
  return (
    isObject(value) &&
    typeof value.tool_name === "string" &&
    "result" in value
  )
}

export function extractAssistantTransactions(
  toolName: unknown,
  toolResult: unknown,
): AssistantTransaction[] | null {
  const executions: ToolExecution[] = []

  // Demo Mode returns a list of tool executions.
  if (Array.isArray(toolResult)) {
    for (const item of toolResult) {
      if (isToolExecution(item)) {
        executions.push(item)
      }
    }
  }

  // OpenAI Mode currently exposes the first result directly.
  if (
    executions.length === 0 &&
    typeof toolName === "string"
  ) {
    executions.push({
      tool_name: toolName,
      result: toolResult,
    })
  }

  const transactionExecution = executions.find(
    (execution) =>
      TRANSACTION_TOOL_NAMES.has(
        execution.tool_name
      )
  )

  if (!transactionExecution) {
    return null
  }

  if (
    !isAssistantTransactionList(
      transactionExecution.result
    )
  ) {
    return null
  }

  return transactionExecution.result
}
