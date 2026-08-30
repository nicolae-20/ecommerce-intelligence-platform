from database import get_customers


customers = get_customers()

for customer in customers:
    print(customer)