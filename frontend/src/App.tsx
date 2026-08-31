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

function App() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [monthlyRevenue, setMonthlyRevenue] = useState<MonthlyRevenue[]>([])
  const [categoryProfit, setCategoryProfit] = useState<CategoryProfit[]>([])
  const [overview, setOverview] = useState<Overview | null>(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    Promise.all([
      fetch("http://127.0.0.1:8000/customers/top?limit=5"),
      fetch("http://127.0.0.1:8000/analytics/monthly-revenue"),
      fetch("http://127.0.0.1:8000/analytics/profit-by-category"),
      fetch("http://127.0.0.1:8000/analytics/overview"),
    ])
      .then(async ([
        customersResponse,
        revenueResponse,
        profitResponse,
        overviewResponse,
      ]) => {
        if (
          !customersResponse.ok ||
          !revenueResponse.ok ||
          !profitResponse.ok ||
          !overviewResponse.ok
        ) {
          throw new Error("Failed to load dashboard data")
        }

        const [
          customersData,
          revenueData,
          profitData,
          overviewData,
        ] = await Promise.all([
          customersResponse.json(),
          revenueResponse.json(),
          profitResponse.json(),
          overviewResponse.json(),
        ])

        setCustomers(customersData)
        setMonthlyRevenue(revenueData)
        setCategoryProfit(profitData)
        setOverview(overviewData)
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

  if (!overview) {
    return <div className="error-message">No overview data available.</div>
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
