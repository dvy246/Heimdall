import os
import re
import shutil
from pathlib import Path
from typing import List, Union
from langchain.prompts import PromptTemplate
from langchain.retrievers import EnsembleRetriever, BaseRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.tools import tool
from src.config.settings import model
from src.config.logging_config import logger

def clean_financial_text(text: str) -> str:
    """
    Cleans up messy financial text by removing extra whitespace and commas in numbers.

    Args:
        text (str): The input financial text.

    Returns:
        str: The cleaned text.
    """
    logger.debug("Cleaning financial text.")
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'(\d),(\d)', r'\1\2', text)
    return text.strip()

def better_chunking(text: str) -> List[str]:
    """
    Chunks text using a semantic chunker for shorter texts and a recursive character splitter for longer texts.

    Args:
        text (str): The text to be chunked.

    Returns:
        List[str]: A list of text chunks.

    Raises:
        ValueError: If the Google API key is not set.
    """
    logger.info("Performing smart chunking on text.")
    google_api_key = os.getenv("google")
    if not google_api_key:
        logger.error("Google API key not found in environment variables for embeddings.")
        raise ValueError("Google API key is not set in environment variables.")

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=google_api_key)
    cleaned_text = clean_financial_text(text=text)
    
    if len(cleaned_text.split()) < 800:
        logger.debug("Using SemanticChunker for text splitting.")
        semantic_splitter = SemanticChunker(embeddings=embeddings)
        return semantic_splitter.split_text(cleaned_text)
    else:
        logger.debug("Using RecursiveCharacterTextSplitter for text splitting.")
        recursive_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        return recursive_splitter.split_text(cleaned_text)

def chunk_metadata(chunks: List[str], ticker: str) -> List[Document]:
    """
    Adds metadata to each text chunk, creating a list of Document objects.

    Args:
        chunks (List[str]): A list of text chunks.
        ticker (str): The stock ticker symbol associated with the text.

    Returns:
        List[Document]: A list of Document objects with metadata.
    """
    logger.info(f"Adding metadata to {len(chunks)} chunks for ticker: {ticker}")
    return [
        Document(
            page_content=chunk,
            metadata={
                "chunk_id": i, "ticker": ticker,
                'word_count': len(chunk.split()),
                "contains_numbers": bool(re.search(r'\d+', chunk))
            }
        ) for i, chunk in enumerate(chunks)
    ]

def create_hybrid_retriever(vectorstore: Chroma) -> BaseRetriever:
    """
    Creates a hybrid retriever using BM25 for keyword search and a vector store for semantic search.

    Args:
        vectorstore (Chroma): The Chroma vector store instance.

    Returns:
        BaseRetriever: An ensemble retriever combining BM25 and vector search.
    """
    logger.info("Creating hybrid retriever.")
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    
    try:
        docs_from_db = vectorstore.get()["documents"]
        if not docs_from_db:
            logger.warning("No documents found in the vector store for BM25 retriever.")
            return vector_retriever
        
        docs = [Document(page_content=d) for d in docs_from_db]
        bm25_retriever = BM25Retriever.from_documents(docs)
        bm25_retriever.k = 10
        ensemble_retriever = EnsembleRetriever(retrievers=[vector_retriever, bm25_retriever], weights=[0.6, 0.4])
        logger.info("Hybrid retriever created successfully.")
        return ensemble_retriever
    except Exception as e:
        logger.error(f"Error creating BM25 retriever, falling back to vector retriever only: {e}", exc_info=True)
        return vector_retriever

@tool(description='Ingests report data into a vector store for a given ticker.')
def ingest_data_filling(report_text: str, ticker: str) -> str:
    """
    Ingests company information, chunks it, and stores it into a Chroma vector store.

    Args:
        report_text (str): The full text of the report to ingest.
        ticker (str): The stock ticker symbol of the company.

    Returns:
        str: A confirmation message or an error message.

    Raises:
        ValueError: If the Google API key is not set.
    """
    logger.info(f"Starting data ingestion for ticker: {ticker}")
    google_api_key = os.getenv("google")
    if not google_api_key:
        logger.error("Google API key not found in environment variables for ingestion.")
        raise ValueError("Google API key is not set in environment variables.")

    try:
        path = Path("INDEXED") / ticker
        if path.exists():
            logger.warning(f"Existing index found for {ticker}. Removing before re-ingestion.")
            shutil.rmtree(path)
        
        path.mkdir(parents=True, exist_ok=True)
        
        splits = better_chunking(report_text)
        meta_data_chunks = chunk_metadata(splits, ticker)
        
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=google_api_key)
        vectorstore = Chroma.from_documents(meta_data_chunks, embeddings, persist_directory=str(path))
        vectorstore.persist()
        logger.info(f"Successfully ingested {len(meta_data_chunks)} chunks for {ticker}.")
        return f"Successfully ingested 10-K for {ticker}"
    except Exception as e:
        logger.critical(f"An unexpected error occurred during data ingestion for {ticker}: {e}", exc_info=True)
        return f"Error: An unexpected error occurred during data ingestion: {str(e)}"

@tool(description='Asks a question from the indexed vector store for a given ticker.')
def query_data(ticker: str, query: str) -> str:
    """
    Queries the vector store for a given company and returns a model-generated answer based on the retrieved context.

    Args:
        ticker (str): The stock ticker symbol of the company.
        query (str): The question to ask the vector store.

    Returns:
        str: The answer to the query or an error message.

    Raises:
        ValueError: If the Google API key is not set.
    """
    logger.info(f"Querying data for ticker: {ticker} with query: '{query}'")
    google_api_key = os.getenv("google")
    if not google_api_key:
        logger.error("Google API key not found in environment variables for querying.")
        raise ValueError("Google API key is not set in environment variables.")

    try:
        path = Path("INDEXED") / ticker
        if not path.exists():
            logger.warning(f"No vector store found for ticker: {ticker}")
            return "There is no vector store for this ticker yet. Please ingest data first."

        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=google_api_key)
        vectorstore = Chroma(persist_directory=str(path), embedding_function=embeddings)
        retriever = create_hybrid_retriever(vectorstore)
        
        docs = retriever.get_relevant_documents(query)
        if not docs:
            logger.warning(f"No relevant documents found for query: '{query}'")
            return "No relevant information found to answer the question."

        context = "\n\n".join([f"[Source {i+1}] {doc.page_content}" for i, doc in enumerate(docs)])
        
        prompt = PromptTemplate(
            template="Answer the question based on the context below.\n\nContext:\n{context}\n\nQuestion:\n{query}",
            input_variables=["context", "query"],
        )
        
        final_prompt = prompt.format(context=context, query=query)
        response = model.invoke(final_prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        logger.info(f"Successfully generated answer for query: '{query}'")
        return answer
    except Exception as e:
        logger.critical(f"An unexpected error occurred during data querying for {ticker}: {e}", exc_info=True)
        return f"Error: An unexpected error occurred during data querying: {str(e)}"
