import { useEffect, useState } from "react"
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import "./App.css"
import { AssistantTransactionTable } from "./components/AssistantTransactionTable"
import { AssistantSuggestedQuestions } from "./components/AssistantSuggestedQuestions"
import {
  extractAssistantTransactions,
  type AssistantTransaction,
} from "./components/assistantResults"

type Customer = {
  customer_name: string
  total_revenue: number
}

type MonthlyRevenue = {
  order_month: string
  monthly_revenue: number
}

type CategoryProfit = {
  category_name: string
  revenue: number
  cost: number
  profit: number
}

type Overview = {
  total_revenue: number
  total_orders: number
  total_customers: number
  average_order_value: number
}

type FinancialSummary = {
  total_revenue: number
  total_cogs: number
  gross_profit: number
  gross_margin: number
}

type AccountingInsight = {
  type: string
  title: string
  message: string
}

type BookkeepingSummary = {
  total_revenue: number
  total_expenses: number
  net_movement: number
  transactions_requiring_review: number
}


type ReviewTransaction = {
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
  ai_review_status: string
}

type BookkeepingCategory = {
  category_id: number
  account_code: string
  account_name: string
  account_type: string
}

type ReconciliationReviewItem = {
  bank_transaction_id: number
  bank_date: string
  bank_description: string | null
  bank_amount: number
  status: string
  financial_transaction_id: number | null
  match_type: string
  match_confidence: number
  system_date: string | null
  system_description: string | null
  system_amount: number | null
}

type AuditLogItem = {
  audit_id: number
  bank_transaction_id: number | null
  financial_transaction_id: number | null
  action: string
  details: string | null
  created_at: string
}

function App() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [monthlyRevenue, setMonthlyRevenue] = useState<MonthlyRevenue[]>([])
  const [categoryProfit, setCategoryProfit] = useState<CategoryProfit[]>([])
  const [overview, setOverview] = useState<Overview | null>(null)
  const [financialSummary, setFinancialSummary] =
  useState<FinancialSummary | null>(null)
  const [accountingInsights, setAccountingInsights] =
  useState<AccountingInsight[]>([])
  const [bookkeepingSummary, setBookkeepingSummary] =
  useState<BookkeepingSummary | null>(null)
  const [reviewQueue, setReviewQueue] =
  useState<ReviewTransaction[]>([])
  const [aiReviewQueue, setAiReviewQueue] =
  useState<ReviewTransaction[]>([])
  const [bookkeepingCategories, setBookkeepingCategories] =
  useState<BookkeepingCategory[]>([])
  const [selectedCategories, setSelectedCategories] =
  useState<Record<number, number | "">>({})
  const [reconciliationReview, setReconciliationReview] =
  useState<ReconciliationReviewItem[]>([])
  const [auditLog, setAuditLog] = useState<AuditLogItem[]>([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [assistantQuestion, setAssistantQuestion] = useState("")
  const [assistantResponse, setAssistantResponse] = useState("")
  const [assistantError, setAssistantError] = useState("")
  const [assistantTransactions, setAssistantTransactions] =
    useState<AssistantTransaction[] | null>(null)
  const [assistantLoading, setAssistantLoading] = useState(false)

  useEffect(() => {
    Promise.all([
      fetch("http://127.0.0.1:8000/customers/top?limit=5"),
      fetch("http://127.0.0.1:8000/analytics/monthly-revenue"),
      fetch("http://127.0.0.1:8000/analytics/profit-by-category"),
      fetch("http://127.0.0.1:8000/analytics/overview"),
      fetch("http://127.0.0.1:8000/analytics/financial-summary"),
      fetch("http://127.0.0.1:8000/analytics/accounting-insights"),
      fetch("http://127.0.0.1:8000/bookkeeping/summary"),
      fetch("http://127.0.0.1:8000/bookkeeping/review-queue"),
      fetch("http://127.0.0.1:8000/bookkeeping/ai-review-queue"),
      fetch("http://127.0.0.1:8000/bookkeeping/categories"),
      fetch(
      "http://127.0.0.1:8000/bookkeeping/reconciliation-review"
),
      fetch("http://127.0.0.1:8000/bookkeeping/audit-log"),
      
    ])
      .then(async ([
  customersResponse,
  revenueResponse,
  profitResponse,
  overviewResponse,
  financialSummaryResponse,
  accountingInsightsResponse,
  bookkeepingSummaryResponse,
  reviewQueueResponse,
  aiReviewQueueResponse,
  categoriesResponse,
  reconciliationReviewResponse,
  auditLogResponse,
]) => {
  if (
    !customersResponse.ok ||
    !revenueResponse.ok ||
    !profitResponse.ok ||
    !overviewResponse.ok ||
    !financialSummaryResponse.ok ||
    !accountingInsightsResponse.ok ||
    !bookkeepingSummaryResponse.ok ||
    !reviewQueueResponse.ok ||
    !aiReviewQueueResponse.ok ||
    !categoriesResponse.ok ||
    !reconciliationReviewResponse.ok ||
    !auditLogResponse.ok
  ) {
    throw new Error("Failed to load dashboard data")
  }

  const [
    customersData,
    revenueData,
    profitData,
    overviewData,
    financialSummaryData,
    accountingInsightsData,
    bookkeepingSummaryData,
    reviewQueueData,
    aiReviewQueueData,
    categoriesData,
    reconciliationReviewData,
    auditLogData,
  ] = await Promise.all([
    customersResponse.json(),
    revenueResponse.json(),
    profitResponse.json(),
    overviewResponse.json(),
    financialSummaryResponse.json(),
    accountingInsightsResponse.json(),
    bookkeepingSummaryResponse.json(),
    reviewQueueResponse.json(),
    aiReviewQueueResponse.json(),
    categoriesResponse.json(),
    reconciliationReviewResponse.json(),
    auditLogResponse.json(),
  ])

  setCustomers(customersData)
  setMonthlyRevenue(revenueData)
  setCategoryProfit(profitData)
  setOverview(overviewData)
  setFinancialSummary(financialSummaryData)
  setAccountingInsights(accountingInsightsData)
  setBookkeepingSummary(bookkeepingSummaryData)
  setReviewQueue(reviewQueueData)
  setAiReviewQueue(aiReviewQueueData)
  setBookkeepingCategories(categoriesData)
  setReconciliationReview(reconciliationReviewData)
  setAuditLog(auditLogData)
  setLoading(false)
})
      .catch((error) => {
  console.error("Dashboard load error:", error)
  setError(
    error instanceof Error
      ? error.message
      : "Could not load dashboard data"
  )
  setLoading(false)
})
  }, [])

  if (loading) {
    return <div className="status-message">Loading dashboard...</div>
  }

  if (error) {
    return <div className="error-message">{error}</div>
  }

  if (!overview || !financialSummary || !bookkeepingSummary) {
  return <div className="error-message">No financial data available.</div>
}

const handleApprove = async (transactionId: number) => {
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/bookkeeping/transactions/${transactionId}/approve`,
      {
        method: "POST",
      }
    )

    if (!response.ok) {
      throw new Error("Failed to approve transaction")
    }

    setReviewQueue((currentQueue) =>
      currentQueue.filter(
        (transaction) => transaction.transaction_id !== transactionId
      )
    )

    setBookkeepingSummary((currentSummary) => {
      if (!currentSummary) {
        return currentSummary
      }

      return {
        ...currentSummary,
        transactions_requiring_review:
          Math.max(
            0,
            currentSummary.transactions_requiring_review - 1
          ),
      }
    })
  } catch {
    setError("Could not approve transaction")
  }
}

const handleAssignCategory = async (
  transactionId: number,
  categoryId: number
) => {
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/bookkeeping/transactions/${transactionId}/category/${categoryId}`,
      {
        method: "POST",
      }
    )

    if (!response.ok) {
      throw new Error("Failed to assign category")
    }

    setReviewQueue((currentQueue) =>
      currentQueue.filter(
        (transaction) =>
          transaction.transaction_id !== transactionId
      )
    )

    setBookkeepingSummary((currentSummary) => {
      if (!currentSummary) {
        return currentSummary
      }

      return {
        ...currentSummary,
        transactions_requiring_review:
          Math.max(
            0,
            currentSummary.transactions_requiring_review - 1
          ),
      }
    })

    setSelectedCategories((current) => {
      const updated = { ...current }
      delete updated[transactionId]
      return updated
    })
  } catch {
    setError("Could not assign transaction category")
  }
}

const handleReject = async (transactionId: number) => {
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/bookkeeping/transactions/${transactionId}/reject`,
      {
        method: "POST",
      }
    )

    if (!response.ok) {
      throw new Error("Failed to reject transaction")
    }

    const rejectedTransaction = reviewQueue.find(
      (transaction) => transaction.transaction_id === transactionId
    )

    setReviewQueue((currentQueue) =>
      currentQueue.map((transaction) =>
        transaction.transaction_id === transactionId
          ? {
              ...transaction,
              ai_suggested_category: null,
              ai_confidence: null,
            }
          : transaction
      )
    )

    if (!rejectedTransaction) {
      return
    }
  } catch {
    setError("Could not reject transaction")
  }
}

const handleCancel = async (transactionId: number) => {
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/bookkeeping/transactions/${transactionId}/cancel-reject`,
      {
        method: "POST",
      }
    )

    if (!response.ok) {
      throw new Error("Failed to cancel rejection")
    }

    const reviewResponse = await fetch(
  "http://127.0.0.1:8000/bookkeeping/ai-review-queue"
)

    if (!reviewResponse.ok) {
      throw new Error("Failed to refresh review queue")
    }

    const refreshedQueue = await reviewResponse.json()

    setReviewQueue(refreshedQueue)
  } catch {
    setError("Could not cancel rejection")
  }
}

const handleConfirmReconciliation = async (
  bankTransactionId: number
) => {
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/bookkeeping/reconciliation/${bankTransactionId}/confirm`,
      {
        method: "POST",
      }
    )

    if (!response.ok) {
      throw new Error("Failed to confirm reconciliation")
    }

    setReconciliationReview((current) =>
      current.filter(
        (item) =>
          item.bank_transaction_id !== bankTransactionId
      )
    )
  } catch {
    setError("Could not confirm reconciliation")
  }
}

const handleRejectReconciliation = async (
  bankTransactionId: number
) => {
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/bookkeeping/reconciliation/${bankTransactionId}/reject`,
      {
        method: "POST",
      }
    )

    if (!response.ok) {
      throw new Error("Failed to reject reconciliation")
    }

    setReconciliationReview((current) =>
      current.map((item) =>
        item.bank_transaction_id === bankTransactionId
          ? {
              ...item,
              financial_transaction_id: null,
              match_type: "NO_MATCH",
              match_confidence: 0,
            }
          : item
      )
    )
  } catch {
    setError("Could not reject reconciliation")
  }
}

const handleInvestigateReconciliation = async (
  bankTransactionId: number
) => {
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/bookkeeping/reconciliation/${bankTransactionId}/investigate`,
      {
        method: "POST",
      }
    )

    if (!response.ok) {
      throw new Error("Failed to investigate reconciliation")
    }

    setReconciliationReview((current) =>
      current.filter(
        (item) =>
          item.bank_transaction_id !== bankTransactionId
      )
    )
  } catch {
    setError("Could not investigate reconciliation")
  }
}

const handleRunReconciliation = async () => {
  try {
    const response = await fetch(
      "http://127.0.0.1:8000/bookkeeping/reconciliation/run",
      {
        method: "POST",
      }
    )

    if (!response.ok) {
      throw new Error("Failed to run reconciliation")
    }

    const reviewResponse = await fetch(
      "http://127.0.0.1:8000/bookkeeping/reconciliation-review"
    )

    if (!reviewResponse.ok) {
      throw new Error("Failed to refresh reconciliation review")
    }

    const reviewData = await reviewResponse.json()
    console.log("REFRESHED REVIEW QUEUE:", reviewData)
    console.log(
  "REVIEW QUEUE COUNT:",
  reviewData.length
)

console.log(
  "REVIEW QUEUE DATA:",
  reviewData
)
    setReconciliationReview(reviewData)

    const auditResponse = await fetch(
      "http://127.0.0.1:8000/bookkeeping/audit-log"
    )

    if (!auditResponse.ok) {
      throw new Error("Failed to refresh audit log")
    }

    const auditData = await auditResponse.json()

    setAuditLog(auditData)
  } catch {
    setError("Could not run reconciliation")
  }
}

const handleAICategorize = async () => {
  console.log("AI CATEGORIZE BUTTON CLICKED")

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/bookkeeping/ai-categorize",
      {
        method: "POST",
      }
    )

    console.log("AI CATEGORIZE RESPONSE:", response.status)

    if (!response.ok) {
      throw new Error("Failed to run AI categorization")
    }

    const reviewResponse = await fetch(
      "http://127.0.0.1:8000/bookkeeping/review-queue"
    )

    console.log(
      "REVIEW QUEUE RESPONSE:",
      reviewResponse.status
    )

    if (!reviewResponse.ok) {
      throw new Error("Failed to refresh review queue")
    }

    const reviewData = await reviewResponse.json()
    
    setAiReviewQueue(reviewData)

    console.log("REFRESHED REVIEW QUEUE:", reviewData)

    

    const auditResponse = await fetch(
      "http://127.0.0.1:8000/bookkeeping/audit-log"
    )

    console.log(
      "AUDIT RESPONSE:",
      auditResponse.status
    )

    if (!auditResponse.ok) {
      throw new Error("Failed to refresh audit log")
    }

    const auditData = await auditResponse.json()

    setAuditLog(auditData)
  } catch (error) {
    console.error("AI categorization error:", error)

    setError(
      error instanceof Error
        ? error.message
        : "Could not run AI categorization"
    )
  }
}

const handleAskAssistant = async (
  questionOverride?: string,
) => {
  const question = (
    questionOverride ?? assistantQuestion
  ).trim()

  if (!question || assistantLoading) {
    return
  }

  if (questionOverride !== undefined) {
    setAssistantQuestion(question)
  }

  setAssistantLoading(true)
  setAssistantError("")
  setAssistantResponse("")
  setAssistantTransactions(null)

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/bookkeeping/ai-assistant",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question,
        }),
      }
    )

    if (!response.ok) {
      const errorData: unknown = await response
        .json()
        .catch(() => null)

      let errorMessage =
        `AI Assistant request failed (${response.status})`

      if (
        errorData &&
        typeof errorData === "object" &&
        "detail" in errorData &&
        typeof errorData.detail === "string"
      ) {
        errorMessage = errorData.detail
      }

      throw new Error(errorMessage)
    }

    const data: unknown = await response.json()

    if (
      !data ||
      typeof data !== "object" ||
      !("message" in data) ||
      typeof data.message !== "string" ||
      !data.message.trim()
    ) {
      throw new Error(
        "AI Assistant returned an invalid response"
      )
    }

    setAssistantResponse(data.message)

    const toolName =
      "tool_name" in data
        ? data.tool_name
        : null

    const toolResult =
      "tool_result" in data
        ? data.tool_result
        : null

    setAssistantTransactions(
      extractAssistantTransactions(
        toolName,
        toolResult,
      )
    )
  } catch (error) {
    console.error("AI Assistant error:", error)

    setAssistantError(
      error instanceof Error
        ? error.message
        : "Could not contact AI Assistant"
    )
  } finally {
    setAssistantLoading(false)
  }
}


  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <h1>E-commerce Intelligence Dashboard</h1>
        <p>Financial and business performance overview</p>
      </header>

      <section>
        <h2>Financial Overview</h2>

        <div className="kpi-grid">
          <div className="kpi-card">
            <span>Total Revenue</span>
            <strong>€{overview.total_revenue.toFixed(2)}</strong>
          </div>

          <div className="kpi-card">
            <span>Total Orders</span>
            <strong>{overview.total_orders}</strong>
          </div>

          <div className="kpi-card">
            <span>Total Customers</span>
            <strong>{overview.total_customers}</strong>
          </div>

          <div className="kpi-card">
            <span>Average Order Value</span>
            <strong>€{overview.average_order_value.toFixed(2)}</strong>
          </div>
        </div>
      </section>
            <section>
        <h2>Financial Performance</h2>

        <div className="kpi-grid">
          <div className="kpi-card">
            <span>Revenue</span>
            <strong>
              €{financialSummary.total_revenue.toFixed(2)}
            </strong>
          </div>

          <div className="kpi-card">
            <span>COGS</span>
            <strong>
              €{financialSummary.total_cogs.toFixed(2)}
            </strong>
          </div>

          <div className="kpi-card">
            <span>Gross Profit</span>
            <strong>
              €{financialSummary.gross_profit.toFixed(2)}
            </strong>
          </div>

          <div className="kpi-card">
            <span>Gross Margin</span>
            <strong>
              {financialSummary.gross_margin.toFixed(2)}%
            </strong>
          </div>
        </div>
      </section>
      <section>
  <h2>Bookkeeping Summary</h2>

  <div className="kpi-grid">
    <div className="kpi-card">
      <span>Revenue</span>
      <strong>
        €{bookkeepingSummary.total_revenue.toFixed(2)}
      </strong>
    </div>

    <div className="kpi-card">
      <span>Expenses</span>
      <strong>
        €{bookkeepingSummary.total_expenses.toFixed(2)}
      </strong>
    </div>

    <div className="kpi-card">
      <span>Net Movement</span>
      <strong>
        €{bookkeepingSummary.net_movement.toFixed(2)}
      </strong>
    </div>

    <div className="kpi-card">
      <span>Needs Review</span>
      <strong>
        {bookkeepingSummary.transactions_requiring_review}
      </strong>
    </div>
  </div>
</section>
<section className="dashboard-card">
  <h2>AI Assistant</h2>

  <div className="assistant-input-row">
    <input
      type="text"
      value={assistantQuestion}
      onChange={(event) =>
        setAssistantQuestion(event.target.value)
      }
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          event.preventDefault()
          void handleAskAssistant()
        }
      }}
      disabled={assistantLoading}
      placeholder="Ask about bookkeeping, AI review, reconciliation, or audit activity..."
    />

    <button
      className="assistant-button"
      onClick={() => {
        void handleAskAssistant()
      }}
      disabled={
        assistantLoading || !assistantQuestion.trim()
      }
    >
      {assistantLoading ? "Asking..." : "Ask Assistant"}
    </button>
  </div>

  <AssistantSuggestedQuestions
    disabled={assistantLoading}
    onSelect={(question) => {
      void handleAskAssistant(question)
    }}
  />

  {assistantError && (
    <div className="error-message" role="alert">
      {assistantError}
    </div>
  )}

  {assistantTransactions !== null && (
    <AssistantTransactionTable
      transactions={assistantTransactions}
    />
  )}

  {assistantResponse && (
    <div
      className="assistant-response"
      role="status"
      aria-live="polite"
    >
      <strong>
        {assistantTransactions !== null
          ? "Assistant summary"
          : "Assistant"}
      </strong>
      <p style={{ whiteSpace: "pre-wrap" }}>
        {assistantResponse}
      </p>
    </div>
  )}
</section>
<section className="dashboard-card">
  <h2>AI Categorization Review</h2>


  <button
  className="ai-categorize-button"
  onClick={handleAICategorize}
>
  AI Categorize Transactions
</button>

  {aiReviewQueue.map((transaction) => (
    <div className="review-row" key={transaction.transaction_id}>
      <div className="review-main">
        <strong>{transaction.description}</strong>

        <span>
          {transaction.vendor || "No vendor"} ·{" "}
          {transaction.transaction_type}
        </span>
      </div>

      <div className="review-details">
        <strong>
          €{transaction.amount.toFixed(2)}
        </strong>

        <span>
          AI:{" "}
          {transaction.ai_suggested_category || "No suggestion"}
        </span>

        <span>
          Confidence:{" "}
          {transaction.ai_confidence !== null
            ? `${(transaction.ai_confidence * 100).toFixed(0)}%`
            : "N/A"}
        </span>
        <span>
  AI Review: {transaction.ai_review_status}
</span>

        <span>
          {transaction.reconciliation_status}
        </span>

        <span>
          {transaction.status}
        </span>
        
{transaction.ai_suggested_category ? (
  <>
    <button
      className="approve-button"
      onClick={() => handleApprove(transaction.transaction_id)}
    >
      Approve
    </button>

    <button
      className="reject-button"
      onClick={() => handleReject(transaction.transaction_id)}
    >
      Reject
    </button>
  </>
) : (
  <>
  <button
  className="cancel-button"
  onClick={() => handleCancel(transaction.transaction_id)}
>
  Cancel
</button>
    <select
      value={selectedCategories[transaction.transaction_id] ?? ""}
      onChange={(event) => {
        const value = event.target.value

        setSelectedCategories((current) => ({
          ...current,
          [transaction.transaction_id]:
            value === "" ? "" : Number(value),
        }))
      }}
    >
      <option value="">Select category</option>

      {bookkeepingCategories.map((category) => (
  <option
    key={category.category_id}
    value={category.category_id}
  >
    {category.account_code} — {category.account_name}
  </option>
))}
    </select>

    <button
      className="save-category-button"
      disabled={!selectedCategories[transaction.transaction_id]}
      onClick={() => {
        const categoryId =
          selectedCategories[transaction.transaction_id]

        if (typeof categoryId === "number") {
          handleAssignCategory(
            transaction.transaction_id,
            categoryId
          )
        }
      }}
    >
      Save Category
    </button>
  </>
)}

      </div>
    </div>
  ))}
</section>
<section className="dashboard-card">
  <h2>Reconciliation Review</h2>

  <button
  className="run-reconciliation-button"
  onClick={handleRunReconciliation}
>
  Run Reconciliation
</button>

  {reconciliationReview.length === 0 ? (
    <p className="empty-state">
      No reconciliation items require review.
    </p>
  ) : (
    reconciliationReview.map((item) => (
      <div
        className="review-row"
        key={item.bank_transaction_id}
      >
        <div className="review-main">
          <strong>
            {item.bank_description || "No description"}
          </strong>

          <span>
            {new Date(item.bank_date).toLocaleDateString()} · Bank transaction
          </span>
        </div>

        <div className="review-details">
          <strong>
            €{item.bank_amount.toFixed(2)}
          </strong>

          <span>
            {item.match_type}
          </span>

          <span>
            Confidence:{" "}
            {(item.match_confidence * 100).toFixed(0)}%
          </span>

          {item.system_description ? (
            <span>
              Possible match: {item.system_description}
            </span>
          ) : (
            <span>
              No matching transaction found
            </span>
          )}

          {item.system_amount !== null && (
            <span>
              System amount: €{item.system_amount.toFixed(2)}
            </span>
          )}
          {item.match_type === "POSSIBLE_MATCH" && (
  <>
    <button
      className="confirm-match-button"
      onClick={() =>
        handleConfirmReconciliation(
          item.bank_transaction_id
        )
      }
    >
      Confirm Match
    </button>

    <button
      className="reject-match-button"
      onClick={() =>
        handleRejectReconciliation(
          item.bank_transaction_id
        )
      }
    >
      Reject Match
    </button>
  </>
)}

{item.match_type === "NO_MATCH" && (
  <button
    className="investigate-button"
    onClick={() =>
  handleInvestigateReconciliation(
    item.bank_transaction_id
  )
}
  >
    Investigate
  </button>
)}
        </div>
      </div>
    ))
  )}
</section>
<section className="dashboard-card">
  <h2>Audit Log</h2>

  {auditLog.length === 0 ? (
    <p className="empty-state">
      No audit events recorded.
    </p>
  ) : (
    auditLog.map((event) => (
      <div
        className="review-row"
        key={event.audit_id}
      >
        <div className="review-main">
          <strong>{event.action}</strong>

          <span>
            {new Date(event.created_at).toLocaleString()}
          </span>
        </div>

        <div className="review-details">
          {event.bank_transaction_id !== null && (
            <span>
              Bank transaction: {event.bank_transaction_id}
            </span>
          )}

          {event.financial_transaction_id !== null && (
            <span>
              Financial transaction:{" "}
              {event.financial_transaction_id}
            </span>
          )}

          {event.details && (
            <span>
              {event.details}
            </span>
          )}
        </div>
      </div>
    ))
  )}
</section>
      <section className="dashboard-card">
  <h2>Accounting Insights</h2>

  <div className="insights-list">
    {accountingInsights.map((insight) => (
      <div className="insight-row" key={insight.type}>
        <div>
          <strong>{insight.title}</strong>
          <p>{insight.message}</p>
        </div>
      </div>
    ))}
  </div>
</section>
      <section className="dashboard-card">
        <h2>Monthly Revenue</h2>

        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={monthlyRevenue}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="order_month" />
            <YAxis />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="monthly_revenue"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </section>

      <section className="dashboard-card">
        <h2>Top Customers</h2>

        {customers.map((customer) => (
          <div className="customer-row" key={customer.customer_name}>
            <span className="customer-name">
              {customer.customer_name}
            </span>

            <span className="customer-revenue">
              €{customer.total_revenue.toFixed(2)}
            </span>
          </div>
        ))}
      </section>

      <section className="dashboard-card">
        <h2>Profit by Category</h2>

        {categoryProfit.map((category) => (
          <div className="category-row" key={category.category_name}>
            <span>{category.category_name}</span>

            <strong>€{category.profit.toFixed(2)}</strong>
          </div>
        ))}
      </section>
    </main>
  )
}

export default App
