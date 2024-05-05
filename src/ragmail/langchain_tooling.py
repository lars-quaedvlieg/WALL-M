
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.output_parsers.openai_tools import JsonOutputKeyToolsParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from operator import itemgetter
from typing import List
import pandas as pd

from src.ragmail.query import SYSTEM_PROMPT, query_db
from src.ragmail.rag import get_embeddings, cosine_similarity



class Citation(BaseModel):
    source_id: int = Field(
        ...,
        description="The integer ID of a SPECIFIC source which justifies the answer.",
    )
    quote: str = Field(
        ...,
        description="The VERBATIM quote from the specified source that justifies the answer.",
    )

class quoted_answer(BaseModel):
    """Answer the user question based only on the given sources, and cite the sources used."""

    answer: str = Field(
        ...,
        description="The answer to the user question, which is based only on the given sources.",
    )
    citations: List[Citation] = Field(
        ..., description="Citations from the given sources that justify the answer."
    )

def format_emails_with_id(emails: pd.DataFrame) -> str:
    """Convert emails to a single string.:"""
    formatted = [
        f"Source ID: {i}\nText snippet: {text}"
        for i, text in  emails['chunk_text'].tolist():
    ]
    return "\n\n" + "\n\n".join(formatted)


def generate_with_citations(query: str, context: list[str],
                            model: str = "gpt-3.5-turbo") -> str:
                            #model: str = "gpt-4-turbo-preview") -> str:

    output_parser = JsonOutputKeyToolsParser(
        key_name="quoted_answer", first_tool_only=True
    )

    llm = ChatOpenAI(model=model, temperature=0)

    llm_with_tool = llm.bind_tools(
        [quoted_answer],
        tool_choice="quoted_answer",
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"{SYSTEM_PROMPT}"+":{context}",
            ),
            ("human", "{query}"),
        ]
    )

    format = itemgetter("emails") | RunnableLambda(format_emails_with_id)
    answer = prompt | llm_with_tool | output_parser
    chain = (
        RunnableParallel(question=RunnablePassthrough(), emails=context)
        .assign(context=format)
        .assign(quoted_answer=answer)
        .pick(["quoted_answer"])
    )

    return chain.invoke(query)


def query(table_name: str, prompt: str, filters: dict[str, Any]) -> tuple[str, list[tuple[str, float]]]:

    def get_cos(row: pd.StringDtype) -> float:
        embeddings = list(map(float, row["embeddings"].split(",")))
        return cosine_similarity(embeddings, response_embedding)

    context = query_db(table_name, prompt, filters)
    response = generate_with_citations(prompt, context)

    #response_embedding = get_embeddings(generated_response)
    # replace scores with the similarity score of each chunk to the generated response
    #context["score"] = context.apply(get_cos, axis=1)
    #context = context.sort_values(by=["score"], ascending=False)

    citations_formatted = [f"{c['source_id']: \"{c["quote"]}\"}" for c in response['quoted_answer']['citations']]
    formatted_response = (f"{response['quoted_answer']['answer']}\n\nCitations:\n" +
                          f"{"\n".join(citations_formatted)}")

    referenced_context = []
    for _, row in context.iterrows():
        formatted_chunk = (f"Sender: {row['sender']}\n" +
                           f"Recipient: {row['recipient']}\n" +
                           f"Date: {row['email_date']}\n" +
                           f"Subject: {row['subject']}\n\n" +
                           f"Referenced text:\n\"{row['chunk_text']}\"\n\n" +
                           f"(Similarity score: {row['score']:.2f})\n")

        referenced_context.append((formatted_chunk, row["score"]))

    return formatted_response, referenced_context
