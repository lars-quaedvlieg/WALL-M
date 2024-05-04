from pathlib import Path
import warnings

import pandas as pd
import sqlalchemy
from tqdm.auto import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from langchain_ai21 import AI21SemanticTextSplitter

from parsing import JsonEmailParser


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
    # Config.
    table_name = "dummy2"
    connection_string = "iris://demo:demo@localhost:1972/USER"
    data_dir = Path("data/emails")
    embeddings_dim = 1536  # openai text-embedding-3-small

    # Get raw dataframe.
    data_dir = Path("data/emails")
    email_parser = JsonEmailParser(data_dir)
    df = email_parser.parse()

    # Get chunks.
    df = chunking(df)

    # Add embeddings.
    df = df.iloc[:5, :]  # avoid too many api calls until we go into production
    df["embeddings"] = list(map(get_embeddings, tqdm(df["chunk_text"], desc="Getting embeddings")))
    print(df.keys())
    print(df)

    # Make database.
    # to, from, subject, date, text, thead_id, email_id
    engine = sqlalchemy.create_engine(connection_string)
    print("Creating database")
    with engine.connect() as conn:
        with conn.begin():
            sql = f"""
                    CREATE TABLE {table_name} (
            email_id INT,
            thread_id INT,
            chunk_id INT,
            subject VARCHAR(255),
            sender VARCHAR(255),
            recipient VARCHAR(255),
            email_date DATETIME,
            text VARCHAR(3000),
            chunk_text VARCHAR(3000),
            embeddings VECTOR(DOUBLE, {embeddings_dim})
            )
                    """
            try:
                result = conn.execute(sqlalchemy.text(sql))
            except sqlalchemy.exc.DatabaseError:
                warnings.warn(f"Database {table_name} already exists lol")

    # Insert data.
    print("Inserting data into database")
    with engine.connect() as conn:
        with conn.begin():
            for _, row in df.iterrows():
                sql = sqlalchemy.text(f"""
                    INSERT INTO {table_name} 
                    (email_id, thread_id, chunk_id, subject, sender, recipient, email_date, text, chunk_text, embeddings)
                    VALUES (:email_id, :thread_id, :chunk_id, :subject, :sender, :recipient, :email_date, :text, :chunk_text, TO_VECTOR(:embeddings))
                """)
                data = dict(row)
                data = {key: str(value) for key, value in data.items()}
                conn.execute(sql, data)


if __name__ == "__main__":
    load_dotenv()
    main()
