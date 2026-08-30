from analytics import (
    get_customer_metrics,
    get_monthly_revenue,
    get_top_customers,
)


customers = get_top_customers(5)
monthly_revenue = get_monthly_revenue()
customer_metrics = get_customer_metrics()

print("Top customers:")

for customer in customers:
    print(customer)

print()
print("Monthly revenue:")

for month in monthly_revenue:
    print(month)

print()
print("Customer metrics:")

for customer in customer_metrics:
    print(customer)