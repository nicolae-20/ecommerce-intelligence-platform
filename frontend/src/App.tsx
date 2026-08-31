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
  description: string | null
  amount: number
  category: string | null
  vendor: string | null
  ai_suggested_category: string | null
  ai_confidence: number | null
  reconciliation_status: string
  status: string
}

type BookkeepingCategory = {
  category_id: number
  account_code: string
  account_name: string
  account_type: string
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
  const [bookkeepingCategories, setBookkeepingCategories] =
  useState<BookkeepingCategory[]>([])
  const [selectedCategories, setSelectedCategories] =
  useState<Record<number, number | "">>({})

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

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
      fetch("http://127.0.0.1:8000/bookkeeping/categories"),
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
        categoriesResponse,
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
          !categoriesResponse.ok
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
  categoriesData,
] = await Promise.all([
  customersResponse.json(),
  revenueResponse.json(),
  profitResponse.json(),
  overviewResponse.json(),
  financialSummaryResponse.json(),
  accountingInsightsResponse.json(),
  bookkeepingSummaryResponse.json(),
  reviewQueueResponse.json(),
  categoriesResponse.json(),
])

        setCustomers(customersData)
        setMonthlyRevenue(revenueData)
        setCategoryProfit(profitData)
        setOverview(overviewData)
        setFinancialSummary(financialSummaryData)
        setAccountingInsights(accountingInsightsData)
        setBookkeepingSummary(bookkeepingSummaryData)
        setReviewQueue(reviewQueueData)
        setBookkeepingCategories(categoriesData)
        setLoading(false)
      })
      .catch(() => {
        setError("Could not load dashboard data")
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
      "http://127.0.0.1:8000/bookkeeping/review-queue"
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
  <h2>Transactions Requiring Review</h2>

  {reviewQueue.map((transaction) => (
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
