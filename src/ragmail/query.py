import pandas as pd
import sqlalchemy
from dotenv import load_dotenv
from openai import OpenAI

from src.ragmail.rag import get_embeddings, cosine_similarity

CONNECTION_STRING = "iris://demo:demo@localhost:1972/USER"

SYSTEM_PROMPT = (
    "You are a highly focused assistant tasked with providing accurate, "
    "reliable, and to-the-point answers to questions based solely on the provided context below."
    "Verify your answers against the context to ensure accuracy. "
    "Accurate answers will be rewarded to promote meticulous response formulation."
    "Hallucination of information that isn't in the data will be punished appropriately."
    "Most importantly, tag each of your claims with the correct source chronologically. For example, if you use facts from the first source, you end with a [1], etc."
)

TEMPLATE = (
    "Below, you are given the information that you are permitted to base your facts on. \n"
    "---------------------\n"
    "{context}"
    "\n---------------------\n"
    "Make sure to adhere to the guidelines above. Given this information, please answer the following question: {query}\n"
)



def get_response(query: str, contexts: list[str],
                 model: str = "gpt-4-turbo-preview") -> str:

    assert len(contexts) > 0, "Can't answer without context lol"
    context = "-----\n".join(contexts)
    prompt = TEMPLATE.format(query=query, context=context)
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def get_senders(table_name: str) -> set[str]:
    engine = sqlalchemy.create_engine(CONNECTION_STRING)
    with engine.connect() as conn:
        with conn.begin():
            sql = sqlalchemy.text(f"SELECT DISTINCT sender FROM {table_name}")
            results = conn.execute(sql).fetchall()
    return {result.lower() for result, in results}


def query_db(table_name: str, prompt: str, filters=None) -> pd.DataFrame:
    search_vector = get_embeddings(prompt)  # Convert search phrase into a vector.
    engine = sqlalchemy.create_engine(CONNECTION_STRING)
    with engine.connect() as conn:
        with conn.begin():
            sql = sqlalchemy.text(f"""
                SELECT TOP 8 *, VECTOR_DOT_PRODUCT(embeddings, TO_VECTOR(:search_vector)) AS score
                FROM {table_name}
                ORDER BY score DESC
            """)
            results = conn.execute(sql, {"search_vector": str(search_vector)})
            columns = results.keys()
            context = results.fetchall()
    return pd.DataFrame(context, columns=columns)


def query(table_name: str, prompt: str, filters=None) -> tuple[str, list[tuple[str, float]]]:
    # def get_cos(row: pd.StringDtype) -> float:
    #     embeddings = list(map(float, row["embeddings"].split(",")))
    #     return cosine_similarity(embeddings, response_embedding)


    print(table_name, prompt, filters)
    context = query_db(table_name, prompt, filters)
    generated_response = get_response(prompt, context['chunk_text'].tolist())

    # response_embedding = get_embeddings(generated_response)
    # # replace scores with the similarity score of each chunk to the generated response
    # context["score"] = context.apply(get_cos, axis=1)
    # context = context.sort_values(by=["score"], ascending=False)

    referenced_context = []
    for idx, row in context.iterrows():
        formatted_chunk = (f"Sender: {row['sender']}\n" +
                           f"Recipient: {row['recipient']}\n" +
                           f"Date: {row['email_date']}\n" +
                           f"Subject: {row['subject']}\n\n" +
                           f"Referenced text:\n\"{row['chunk_text']}\"")

        referenced_context.append((formatted_chunk, row["score"]))

    return generated_response, referenced_context

if __name__ == "__main__":
    load_dotenv()

    print(get_senders("dummy2"))

    #response = get_response("What is 2x2?", ["Scientists recently discovered that 2x2=5"])
    #print(response)

    #res = query("dummy2", "fuck you lol")
    #print(res)
    #print(len(res))
    #print("\n\n".join(map(str, res)))
