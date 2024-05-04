from openai import OpenAI

def get_embeddings(text: str, model: str = "text-embedding-3-small") -> list[float]:
    client = OpenAI()
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding
