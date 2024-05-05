
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.output_parsers.openai_tools import JsonOutputKeyToolsParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableLambda,
    RunnableParallel,
    RunnableSerializable,
    RunnablePassthrough,
)
from operator import itemgetter
from typing import List, Any
import pandas as pd

from src.ragmail.query import SYSTEM_PROMPT, query_db
from src.ragmail.rag import get_embeddings, cosine_similarity

from langchain_core.retrievers import BaseRetriever

class EmailRetriever(BaseRetriever):
    def __init__(self, emails, top_k_results: int = 8, **kwargs):
        super().__init__(top_k_results=top_k_results, **kwargs)
        self.metadata = {"emails": emails}
        # Any initialization code goes here

    def _get_relevant_documents(self, query: str) -> list:
        """
        Method to retrieve relevant emails based on the given query.
        """

        contexts = [dict(row) for _, row in self.metadata["emails"].iterrows()]
        return contexts

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

def format_emails_with_id(emails: list[dict]) -> str:
    """Convert emails to a single string.:"""
    formatted = [
        f"Source ID: {i}\nText snippet: {context['chunk_text']}"
        for i, context in enumerate(emails)
    ]
    return "\n\n" + "\n\n".join(formatted)


def generate_with_citations(query: str, context: pd.DataFrame,
                            model: str = "gpt-3.5-turbo") -> str:
                            #model: str = "gpt-4-turbo-preview") -> str:

    output_parser = JsonOutputKeyToolsParser(
        key_name="quoted_answer", first_tool_only=True
    )

    email_retriver = EmailRetriever(context)
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
            ("human", query),
        ]
    )

    format = itemgetter("emails") | RunnableLambda(format_emails_with_id)
    answer = prompt | llm_with_tool | output_parser
    #contexts = {column: context[column].tolist() for column in context.columns}

    #formatted_emails = format_emails_with_id(contexts)
    #quoted_answer = llm_with_tool(formatted_emails)
    #output_parser.apply(quoted_answer)
    #return output_parser(quoted_answer)


    chain = (
        RunnableParallel(question=RunnablePassthrough(), emails=email_retriver)
        .assign(context=format)
        .assign(quoted_answer=answer)
        .pick(["quoted_answer"])
    )
    return chain.invoke(query)


def query(table_name: str, prompt: str, filters: dict[str, Any]) -> tuple[str, list[tuple[str, float]]]:
    context = query_db(table_name, prompt, filters)
    response = generate_with_citations(prompt, context)

    citations_formatted = [f"{c['source_id']}: \"{c['quote']}\"" for c in response['quoted_answer']['citations']]
    citations_formatted = "\n".join(citations_formatted)
    formatted_response = f"{response['quoted_answer']['answer']}\n\nCitations:\n{citations_formatted}"

    referenced_context = []
    for _, row in context.iterrows():
        formatted_chunk = (f"Sender: {row['sender']}\n" +
                           f"Recipient: {row['recipient']}\n" +
                           f"Date: {row['email_date']}\n" +
                           f"Subject: {row['subject']}\n\n" +
                           f"Referenced text:\n\"{row['chunk_text']}\"\n\n" +
                           f"(Similarity score: {float(row['score']):.2f})\n")

        referenced_context.append((formatted_chunk, row["score"]))

    return formatted_response, referenced_context
