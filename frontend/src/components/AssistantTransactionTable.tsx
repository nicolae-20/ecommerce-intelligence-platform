import "./AssistantTransactionTable.css"

import type { AssistantTransaction } from "./assistantResults"

type AssistantTransactionTableProps = {
  transactions: AssistantTransaction[]
}

const eurFormatter = new Intl.NumberFormat("en-IE", {
  style: "currency",
  currency: "EUR",
})

function formatTransactionDate(value: string) {
  const datePart = value.split("T")[0]

  return datePart || value
}

export function AssistantTransactionTable({
  transactions,
}: AssistantTransactionTableProps) {
  if (transactions.length === 0) {
    return (
      <div
        className="assistant-structured-result"
        role="status"
      >
        <strong>Transaction results</strong>
        <p>No matching transactions were found.</p>
      </div>
    )
  }

  return (
    <div
      className="assistant-structured-result"
      role="region"
      aria-label="Assistant transaction results"
    >
      <div className="assistant-result-header">
        <div>
          <strong>Transaction results</strong>
          <span>
            {transactions.length} transaction
            {transactions.length === 1 ? "" : "s"}
          </span>
        </div>
      </div>

      <div className="assistant-table-scroll">
        <table className="assistant-transaction-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Description</th>
              <th>Vendor</th>
              <th className="assistant-amount-cell">
                Amount
              </th>
              <th>Category</th>
              <th>Status</th>
              <th>Reconciliation</th>
            </tr>
          </thead>

          <tbody>
            {transactions.map((transaction) => (
              <tr key={transaction.transaction_id}>
                <td>
                  {formatTransactionDate(
                    transaction.transaction_date
                  )}
                </td>

                <td>
                  <div className="assistant-transaction-main">
                    <strong>
                      {transaction.description}
                    </strong>
                    <span>
                      #{transaction.transaction_id}
                      {" ? "}
                      {transaction.transaction_type}
                    </span>
                  </div>
                </td>

                <td>
                  {transaction.vendor || "No vendor"}
                </td>

                <td className="assistant-amount-cell">
                  {eurFormatter.format(
                    transaction.amount
                  )}
                </td>

                <td>
                  {transaction.category ||
                    "Uncategorized"}
                </td>

                <td>
                  <span className="assistant-status-badge">
                    {transaction.status}
                  </span>
                </td>

                <td>
                  {transaction.reconciliation_status}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
