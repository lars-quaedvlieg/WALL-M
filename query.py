import random
import pandas as pd
from rag import get_embeddings
import sqlalchemy
from dotenv import load_dotenv


TEMPLATE = (
    "We have provided context information below. \n"
    "---------------------\n"
    "{context}"
    "\n---------------------\n"
    "Given this information, please answer the question: {query}\n"
)



def get_response(query: str, context: list[str]) -> str:
    context = "-----\n".join(context)
    prompt = TEMPLATE.format(query=query, context=context)





def query(table_name: str, prompt: str, filters=None) -> pd.DataFrame:

    # Config.
    connection_string = "iris://demo:demo@localhost:1972/USER"
    embeddings_dim = 1536  # openai text-embedding-3-small

    search_vector = get_embeddings(prompt) #.tolist() # Convert search phrase into a vector

    # Query.
    engine = sqlalchemy.create_engine(connection_string)
    with engine.connect() as conn:
        with conn.begin():
                #SELECT TOP 3 *, VECTOR_COSINE(embeddings, TO_VECTOR(:search_vector)) AS score
            sql = sqlalchemy.text(f"""
                SELECT TOP 3 *, VECTOR_DOT_PRODUCT(embeddings, TO_VECTOR(:search_vector)) AS score
                FROM {table_name}
                ORDER BY score DESC
            """)
            results = conn.execute(sql, {"search_vector": str(search_vector)})
            columns = results.keys()
            context = results.fetchall()
    return pd.DataFrame(context, columns=columns)


if __name__ == "__main__":
    load_dotenv()
    res = query("dummy2", "fuck you lol")
    print(res)
    #print(len(res))
    #print("\n\n".join(map(str, res)))
