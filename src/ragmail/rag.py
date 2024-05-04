from openai import OpenAI
import numpy as np
from numpy import dot
from numpy.linalg import norm


def get_embeddings(text: str, model: str = "text-embedding-3-small") -> list[float]:
    client = OpenAI()
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding


def cosine_similarity(embedding1: list[float], embedding2: list[float]) -> float:

    e1 = np.array(embedding1)
    e2 = np.array(embedding2)

    return dot(e1, e2) / (norm(e1) * norm(e2))
