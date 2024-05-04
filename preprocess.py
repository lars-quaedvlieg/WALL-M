from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from langchain_ai21 import AI21SemanticTextSplitter
from parsing import JsonEmailParser


def chunking(df: pd.DataFrame) -> pd.DataFrame:
    chunked_data = []
    splitter = AI21SemanticTextSplitter()
    for i, row in df.iterrows():
        chunks = splitter.split_text(row["doc_text"])
        print(f"Document {i} chunked into {len(chunks)} parts")
        for j, chunk in enumerate(chunks):
            chunked_row = row.copy()
            chunked_row["chunk_id"] = j
            chunked_row["chunk_text"] = chunk
            chunked_data.append(chunked_row)
    return pd.DataFrame(chunked_data)


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
    # TODO


if __name__ == "__main__":
    load_dotenv()
    main()
