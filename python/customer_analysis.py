import json
from pathlib import Path


def load_customers(file_path: str) -> list[dict]:
    """Load customer data from a JSON file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_customer_names(customers: list[dict]) -> list[str]:
    """Return full names from customer records."""
    return [
        f"{customer['first_name']} {customer['last_name']}"
        for customer in customers
    ]


def main() -> None:
    customers = load_customers("customers.json")
    names = get_customer_names(customers)

    for name in names:
        print(name)


if __name__ == "__main__":
    main()