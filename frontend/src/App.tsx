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

function App() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [monthlyRevenue, setMonthlyRevenue] = useState<MonthlyRevenue[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [categoryProfit, setCategoryProfit] = useState<CategoryProfit[]>([])

  useEffect(() => {
    Promise.all([
      fetch("http://127.0.0.1:8000/customers/top?limit=5"),
      fetch("http://127.0.0.1:8000/analytics/monthly-revenue"),
      fetch("http://127.0.0.1:8000/analytics/profit-by-category"),
    ])
      .then(async ([customersResponse, revenueResponse, profitResponse]) => {
        if (
  !customersResponse.ok ||
  !revenueResponse.ok ||
  !profitResponse.ok
) {
          throw new Error("Failed to load dashboard data")
        }

        const [customersData, revenueData, profitData] = await Promise.all([
  customersResponse.json(),
  revenueResponse.json(),
  profitResponse.json(),
])

setCustomers(customersData)
setMonthlyRevenue(revenueData)
setCategoryProfit(profitData)
setLoading(false)
      })
      .catch(() => {
        setError("Could not load dashboard data")
        setLoading(false)
      })
  }, [])

  return (
    <div>
      <h1>E-commerce Intelligence Dashboard</h1>

      {loading && <p>Loading...</p>}

      {error && <p>{error}</p>}

      {!loading && !error && (
        <>
          <section>
            <h2>Top Customers</h2>

            {customers.map((customer) => (
              <div key={customer.customer_name}>
                <strong>{customer.customer_name}</strong>
                <span> €{customer.total_revenue.toFixed(2)}</span>
              </div>
            ))}
          </section>

          <section>
  <h2>Monthly Revenue</h2>

  <section>
  <h2>Profit by Category</h2>

  {categoryProfit.map((category) => (
    <div key={category.category_name}>
      <strong>{category.category_name}</strong>
      <span> €{category.profit.toFixed(2)}</span>
    </div>
  ))}
</section>

  <ResponsiveContainer width="100%" height={300}>
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
        </>
      )}
    </div>
  )
}

export default App