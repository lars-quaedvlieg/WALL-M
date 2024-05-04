from pathlib import Path

import pandas as pd
import sqlalchemy
from tqdm.auto import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from langchain_ai21 import AI21SemanticTextSplitter


def chunking(df: pd.DataFrame) -> pd.DataFrame:
    chunked_data = []
    splitter = AI21SemanticTextSplitter()
    for i, row in df.iterrows():
        chunks = splitter.split_text(row["text"])
        print(f"Document {i} chunked into {len(chunks)} parts")
        for j, chunk in enumerate(chunks):
            chunked_row = row.copy()
            chunked_row["chunk_id"] = j
            chunked_row["chunk_text"] = chunk
            chunked_data.append(chunked_row)
    return pd.DataFrame(chunked_data)


def get_embeddings(text: str, model: str = "text-embedding-3-small") -> list[float]:
    client = OpenAI()
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding


def main():
    # Get raw dataframe.
    data = []
    data_dir = Path("data/emails")
    email_parser = JsonEmailParser(data_dir)
    df = email_parser.parse()
    # Get chunks.
    df = chunking(df)
    print(df)

    # Make database.
    # to, from, subject, date, text, thead_id, email_id
    engine = sqlalchemy.create_engine(connection_string)
    with engine.connect() as conn:
        with conn.begin():
            sql = f"""
                    CREATE TABLE {table_name} (
            email_id INT,
            thread_id INT,
            chunk_id INT,
            subject VARCHAR(255),
            to VARCHAR(255),
            from VARCHAR(255),
            date DATETIME,
            text VARCHAR(255),
            chunk_text VARCHAR(255),
            embeddings VECTOR(DOUBLE, {embeddings_dim})
            )
                    """
            result = conn.execute(sqlalchemy.text(sql))

    # Insert data.
    with engine.connect() as conn:
        with conn.begin():
            for _, row in df.iterrows():
                sql = sqlalchemy.text("""
                    INSERT INTO scotch_reviews 
                    (email_id, thread_id, chunk_id, subject, to, from, date, text, chunk_text, embeddings)
                    VALUES (:email_id, :thread_id, :chunk_id, :subject, :to, :from, :date, :text, :chunk_text, TO_VECTOR(:embeddings))
                """)
                data = dict(row)
                data = {key: str(value) for key, value in data.items()}
                conn.execute(sql, data)


if __name__ == "__main__":
    load_dotenv()
    main()
