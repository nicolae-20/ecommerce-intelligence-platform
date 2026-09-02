from database import get_connection


def main() -> None:
    connection = get_connection()

    try:
        print("Successfully connected to Oracle!")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
