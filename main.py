import mailbox

from dotenv import load_dotenv
from llama_iris import IRISVectorStore
from llama_index import StorageContext, SimpleDirectoryReader
from llama_index.indices.vector_store import VectorStoreIndex
#from llama_index.postprocessor.cohere_rerank import CohereRerank



def get_metadata(path: str):
    #email = mailbox.mbox(path)
    #print(email)
    return {"date": "TODO"}


def main():
    # Config.
    prompt = "Hello bro, how are you?" #"What was the author's involvement regarding YC and Arc?" #"What did McCarthy realized about Lisp?" #"What is the author's name?" #"What did the author do growing up?"

    # Init stuff.
    documents = SimpleDirectoryReader(input_dir="data/emails").load_data()
    vector_store = IRISVectorStore.from_params(
        connection_string=f"iris://demo:demo@localhost:1972/USER",
        table_name="temp",
        embed_dim=1536,  # openai embedding dimension
    )

    # Construct database first time.
    #storage_context = StorageContext.from_defaults(vector_store=vector_store)
    #index = VectorStoreIndex.from_documents(documents, storage_context=storage_context,
    #                                    show_progress=True)
    #query_engine = index.as_query_engine(similarity_top_k=1)


    # Build index, we asume we are reconnecting.
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    #storage_context = StorageContext.from_defaults(vector_store=vector_store)
    query_engine = index.as_query_engine()
    print("Number of documents:", len(documents))
    for document in documents:
        index.insert(document=document, storage_context=storage_context)

    # Prompt and print.
    response = query_engine.query(prompt)
    print("PROMPT:", prompt)
    print("RESPONSE:")
    print(response)
    print("="*20)
    print("Sources:")
    for i, source in enumerate(sorted(response.source_nodes, key=lambda source: source.score)):
        print(f"Source {i} (score={source.score:.3f})")
        print(source.text)
        print("-"*10)


if __name__ == "__main__":
    load_dotenv()
    main()
