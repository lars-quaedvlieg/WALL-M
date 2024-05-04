import random

import sqlalchemy


def main():
    # Config.
    table_name = "dummy2"
    connection_string = "iris://demo:demo@localhost:1972/USER"
    embeddings_dim = 1536  # openai text-embedding-3-small

    # Get search_vector.
    search_vector = [random.random() for _ in range(embeddings_dim)]

    # Query.
    engine = sqlalchemy.create_engine(connection_string)
    with engine.connect() as conn:
        with conn.begin():
            sql = sqlalchemy.text(f"""
                SELECT TOP 3 * FROM {table_name}
                ORDER BY VECTOR_DOT_PRODUCT(embeddings, TO_VECTOR(:search_vector)) DESC
            """)
            results = conn.execute(sql, {"search_vector": str(search_vector)}).fetchall()
    print(results)    


if __name__ == "__main__":
    main()
