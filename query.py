import random
from rag import get_embeddings
import sqlalchemy

def query(table_name, prompt, filters=None):

    # Config.
    connection_string = "iris://demo:demo@localhost:1972/USER"
    embeddings_dim = 1536  # openai text-embedding-3-small

    search_vector = get_embeddings(prompt).tolist() # Convert search phrase into a vector

    # Query.
    engine = sqlalchemy.create_engine(connection_string)
    with engine.connect() as conn:
        with conn.begin():
            sql = sqlalchemy.text(f"""
                SELECT TOP 3 * FROM {table_name}
                ORDER BY VECTOR_DOT_PRODUCT(embeddings, TO_VECTOR(:search_vector)) DESC
            """)
            results = conn.execute(sql, {"search_vector": str(search_vector)}).fetchall()

    return results


#if __name__ == "__main__":
#    main()
