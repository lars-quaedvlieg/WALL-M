import pandas as pd
import sqlalchemy
from openai import OpenAI
from dotenv import load_dotenv

from rag import get_embeddings


TEMPLATE = (
    "We have provided context information below. \n"
    "---------------------\n"
    "{context}"
    "\n---------------------\n"
    "Given this information, please answer the question: {query}\n"
)



def get_response(query: str, contexts: list[str],
                 model: str = "gpt-3.5-turbo") -> str:

    assert len(contexts) > 0, "Can't answer without context lol"
    context = "-----\n".join(contexts)
    prompt = TEMPLATE.format(query=query, context=context)
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. You may only respond questions using information from the context provided."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def query(table_name: str, prompt: str, filters=None) -> pd.DataFrame:
    # Config.
    connection_string = "iris://demo:demo@localhost:1972/USER"
    search_vector = get_embeddings(prompt)  # Convert search phrase into a vector.

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
    response = get_response("What is 2x2?", ["Scientists recently discovered that 2x2=5"])
    print(response)
    #res = query("dummy2", "fuck you lol")
    #print(res)
    #print(len(res))
    #print("\n\n".join(map(str, res)))
