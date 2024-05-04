from pathlib import Path
import warnings

import pandas as pd
import sqlalchemy
from tqdm.auto import tqdm
from dotenv import load_dotenv
from langchain_ai21 import AI21SemanticTextSplitter

from src.ragmail.parsing import JsonEmailParser
from src.ragmail.rag import get_embeddings

CONNECTION_STRING = "iris://demo:demo@localhost:1972/USER"

def chunking(df: pd.DataFrame) -> pd.DataFrame:
    chunked_data = []
    splitter = AI21SemanticTextSplitter(chunk_size=800, chunk_overlap=100)
    for i, row in df.iterrows():
        chunks = splitter.split_text(row["text"])
        print(f"Document {i} chunked into {len(chunks)} parts")
        for j, chunk in enumerate(chunks):
            chunked_row = row.copy()
            chunked_row["chunk_id"] = j
            chunked_row["chunk_text"] = chunk
            chunked_data.append(chunked_row)
    return pd.DataFrame(chunked_data)


def table_exists(table_name: str) -> bool:
    engine = sqlalchemy.create_engine(CONNECTION_STRING)
    inspector = sqlalchemy.inspect(engine)
    return inspector.has_table(table_name)


def create_db(data_path, table_name='test'):
    # Config.
    data_dir = Path(data_path)
    embeddings_dim = 1536  # openai text-embedding-3-small

    # Make database.
    # to, from, subject, date, text, thead_id, email_id
    engine = sqlalchemy.create_engine(CONNECTION_STRING)
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
                conn.execute(sqlalchemy.text(sql))
            except sqlalchemy.exc.DatabaseError:
                warnings.warn(f"Database {table_name} already exists, skipping.")
                return table_name



    # Get raw dataframe.
    email_parser = JsonEmailParser(data_dir)
    df = email_parser.parse()

    # Get chunks.
    df = chunking(df)

    # Add embeddings.
    df["embeddings"] = list(map(get_embeddings, tqdm(df["chunk_text"], desc="Getting embeddings")))
    print(df.keys())
    print(df)

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
    print("Done")

    return table_name

if __name__ == "__main__":
    load_dotenv()
    #create_db('../../data/emails')
    print(table_exists("ShazList2131"))
