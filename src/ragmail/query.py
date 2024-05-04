from typing import Any

import pandas as pd
import sqlalchemy
from dotenv import load_dotenv
from openai import OpenAI

from src.ragmail.rag import get_embeddings, cosine_similarity

CONNECTION_STRING = "iris://demo:demo@localhost:1972/USER"
TEMPLATE = (
    "We have provided context information below. \n"
    "---------------------\n"
    "{context}"
    "\n---------------------\n"
    "Given this information, please answer the question: {query}\n"
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
            # {"role": "system", "content": "You are a helpful assistant. You may only respond questions using information from the context provided."},
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


def query_db(table_name: str, prompt: str, filters: dict[str, Any]) -> pd.DataFrame:
    print("infooo", table_name, prompt, filters)

    # Handle filters.
    people_filter = filters["people_filter"]
    dates_filter = filters["dates_filter"]
    if dates_filter == "":
        date1, date2 = "None", "None"
    else:
        date1, date2 = dates_filter
    date1 = None if date1 == "None" else str(date1)
    date2 = None if date2 == "None" else str(date2)
    if people_filter is None and date1 is None and date2 is None:
        filter_query = ""
    else:
        filter_query = "WHERE "
        should_use_and = False
        assert date1 is None or date2 is None or date1 <= date2
        if people_filter is not None:
            filter_query += "subject IN (" + ", ".join(f"'{person}'" for person in people_filter) + ")"
            should_use_and = True
        if date1 is not None:
            filter_query += " AND " if should_use_and else ""
            filter_query += f"email_date >= '{date1}'"
            should_use_and = True
        if date2 is not None:
            filter_query += " AND " if should_use_and else ""
            filter_query += f"email_date <= '{date2}'"
            should_use_and = True

    # Query.
    search_vector = get_embeddings(prompt)  # Convert search phrase into a vector.
    engine = sqlalchemy.create_engine(CONNECTION_STRING)
    with engine.connect() as conn:
        with conn.begin():
            sql = sqlalchemy.text(f"""
                SELECT TOP 8 *, VECTOR_DOT_PRODUCT(embeddings, TO_VECTOR(:search_vector)) AS score
                FROM {table_name}
                {filter_query}
                ORDER BY score DESC
            """)
            results = conn.execute(sql, {"search_vector": str(search_vector)})
            columns = results.keys()
            context = results.fetchall()
    return pd.DataFrame(context, columns=columns)


def fix_citations(response: str, context: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    # Get mapping.
    citation_map = {}
    appear_id = 0
    for i in response.index:
        if f"[{i}]" in response:
            citation_map[i] = appear_id
            appear_id += 1

    # Remap.
    for old_id, new_id in citation_map.items():
        context = context.drop(index=old_id)
        old_response = ""
        while old_response != response:
            old_response = response
            response = response.replace(f"[{old_id}]", f"[{new_id}]")
    context = context.reset_index()
    return response, context
    

def query(table_name: str, prompt: str, filters: dict[str, Any]) -> tuple[str, list[tuple[str, float]]]:

    def get_cos(row: pd.StringDtype) -> float:
        embeddings = list(map(float, row["embeddings"].split(",")))
        return cosine_similarity(embeddings, response_embedding)

    context = query_db(table_name, prompt, filters)
    generated_response = get_response(prompt, context['chunk_text'].tolist())

    generated_response, context = fix_citations(generated_response, context)

    #response_embedding = get_embeddings(generated_response)
    # replace scores with the similarity score of each chunk to the generated response
    #context["score"] = context.apply(get_cos, axis=1)
    #context = context.sort_values(by=["score"], ascending=False)

    referenced_context = []
    for _, row in context.iterrows():
        formatted_chunk = (f"Sender: {row['sender']}\n" +
                           f"Recipient: {row['recipient']}\n" +
                           f"Date: {row['email_date']}\n" +
                           f"Subject: {row['subject']}\n\n" +
                           f"Score: {row['score']}\n\n" +
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
