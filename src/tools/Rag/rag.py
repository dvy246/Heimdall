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
from src.config.looging_config import logger
from src.str_model.strmdls import model_y_n

class SmartFilterWrapper:
    def __init__(self,retriever_base):
        self.retriever=retriever_base
        
    def get_context(self,query:str):
        try:
            logger.info(f"Getting context for query: {query[:50]}...")
            relevant_docs=self.retriever.get_relevant_documents(query)
            context='\n\n'.join([d.page_content for d in relevant_docs] )
            logger.info(f"Retrieved {len(relevant_docs)} documents for context")
            return context
        except Exception as e:
            logger.error(f"Error filtering documents: {e}")
            print(f"An error occurred while filtering documents: {e}")
            
    def filter_documents(self,query:str):
        logger.info(f"Filtering documents for query: {query[:50]}...")
        relevant_documents=self.retriever.get_relevant_documents(query)
        filtered_docs=[]

        for docs in relevant_documents:
            content=docs.page_content
            score=0
 
            if re.search(r'\$[\d,]+|[\d,]+%|\d+\.\d+', content):
                score += 2
            
            # Boost if longer content (more detailed)
            if len(content.split()) > 50:
                score += 1
                
            # Penalize very short content
            if len(content.split()) < 20:
                score -= 1

            filtered_docs.append((docs,score))

        sorted_docs = sorted(filtered_docs, key=lambda x: x[1], reverse=True)
        final_docs=[doc for doc,score in sorted_docs[:5]]
        
        logger.info(f"Filtered to {len(final_docs)} top documents")
        return final_docs
        
def clean_financial_text(text: str) -> str:
    """Clean up messy financial text"""
    logger.debug("Cleaning financial text")
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Fix common OCR errors in financial docs
    text = re.sub(r'(\d),(\d)', r'\1,\2', text)  # Fix number formatting
    logger.debug("Financial text cleaned successfully")
    return text.strip()

def better_chunking(text: str):
    """Chunk text using semantic if short, otherwise recursive splitter"""
    logger.info(f"Starting chunking for text of length {len(text)} characters")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("google")

    )
    text=clean_financial_text(text=text)
    try:
        if len(text.split()) < 800:
            logger.info("Using semantic chunking for shorter text")
            semantic = SemanticChunker(embeddings=embeddings)
            chunks = semantic.split_text(text)
            logger.info(f"✅ Used semantic chunking: {len(chunks)} chunks")
            print(f"✅ Used semantic chunking: {len(chunks)} chunks")
        else:
            logger.info("Using recursive chunking for longer text")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap= 100
            )
            chunks = text_splitter.split_text(text)
            logger.info(f"⚠️ Used recursive chunking: {len(chunks)} chunks")
            print(f"⚠️ Used recursive chunking: {len(chunks)} chunks")
        return chunks
    except Exception as e:
        logger.error(f"Error chunking text: {e}")
        print(f"An error occurred while chunking the text: {e}")
        return [text]

def chunk_metada(chunks:list[str],ticker:str):
    logger.info(f"Creating metadata for {len(chunks)} chunks for ticker {ticker}")
    meta_data_chunks=[]
    for i,chunk in enumerate(chunks):
        doc=Document(
            page_content=chunk,
            metadata={
                "chunk_id": i,
                "ticker": ticker,
                'word_count': len(chunk.split()),
                "contains_numbers": bool(re.search(r'\d+', chunk))
            }
        )
        meta_data_chunks.append(doc)
    logger.info(f"Created {len(meta_data_chunks)} metadata chunks")
    return meta_data_chunks

def enhance_query(original_query: str,ticker:str) -> str:  
        """Enhance the query for better retrieval from a financial document."""
        logger.info(f"Enhancing query for ticker {ticker}: {original_query[:50]}...")
        detected=detect_query_typ(original_query)
        logger.debug(f"Detected query type: {detected}")
        enhancement_prompt = f"""
                You are a financial analysis expert. Enhance this query for better document retrieval.
                
                Original query: "{original_query}"
                Company ticker: {ticker}
                Query type: {detected}
                
                Enhancement rules:
                - If asking about revenue: include terms like "net sales", "total revenue", "operating income"
                - If asking about debt: include "liabilities", "borrowings", "credit facilities"
                - If asking about risks: include "risk factors", "uncertainties", "challenges"
                - Always include the company ticker
                - Make it specific but not too long
                - make sure the ouput aint that long which is easy 
                
                Enhanced query:"""
        try:
                enhanced_query = model.invoke(enhancement_prompt).content.strip()
                logger.info(f"Query enhanced successfully: {enhanced_query[:50]}...")
                return enhanced_query
        except Exception as e:
                logger.error(f"Error enhancing query: {e}")
                return original_query


def create_context_citations(docs):
    """Create context with citations for traceability"""
    logger.debug(f"Creating context citations for {len(docs)} documents")
    context = []
    for i, doc in enumerate(docs, 1):  # Fixed: (i, doc) not (doc, i) and start from 1
        cited_content = f"[Source {i}] {doc.page_content}"
        context.append(cited_content)
    logger.debug("Context citations created successfully")
    return "\n\n".join(context)

def detect_query_typ(query:str):
    logger.debug(f"Detecting query type for: {query[:30]}...")
    try:
        query_lower=query.lower().strip()
        if any(word in query_lower for word in ['revenue', 'sales', 'income']):
                                   logger.debug("Detected financial_performance query type")
                                   return "financial_performance"
        elif any(word in query_lower for word in ['debt', 'liability', 'borrowing']):
                                     logger.debug("Detected financial_position query type")
                                     return "financial_position"
        elif any(word in query_lower for word in ['risk', 'challenge', 'uncertainty']):
                                        logger.debug("Detected risk_analysis query type")
                                        return "risk_analysis"
        else:
            logger.debug("Detected general_inquiry query type")
            return "general_inquiry"
    except Exception as e:
        logger.error(f"Error detecting query type: {e}")
        print(f"An error occurred while detecting query type: {e}")
        return "general_inquiry"


def create_hybrid_retreiver(vectorstore):
    """Create hybrid retriever using BM25 + Vector similarity"""
    logger.info("Creating hybrid retriever")
    try:
        # Vector retriever
        vector_retriever = vectorstore.as_retriever(
            search_kwargs={"k": 10}, search_type="similarity"
        )

        # Pull docs from vector retriever
        docs = vectorstore.get()["documents"]  
        docs = [Document(page_content=d) for d in docs]

        if docs:
            logger.info(f"Creating BM25 retriever with {len(docs)} documents")
            bm25_retriever = BM25Retriever.from_documents(docs)
            bm25_retriever.k = 10

            # Ensemble retriever (hybrid)
            ensemble = EnsembleRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                weights=[0.6, 0.4]
            )
            logger.info("Successfully created hybrid retriever with ensemble")
            return SmartFilterWrapper(ensemble)
        else:
            logger.warning("No documents found, falling back to vector retriever only")
            
        return SmartFilterWrapper(vector_retriever)
    except Exception as e:
        logger.error(f"Error creating hybrid retriever: {e}")
        print(f"An error occurred while creating hybrid retriever: {e}")
        return vectorstore.as_retriever(search_kwargs={"k": 5})


def answer_validator(enhanced_query:str,answer:str,retriever,context:str):
        ''' the job of this function is to validate the answer of the query from the vector store and then matching the context and if they are unsimilar then provide with the new context for the model to answer from '''
        logger.info("Validating answer against context")
        try:
            validation_prompt = f"""
            You are a validation expert. Your job is to determine if the provided 'Answer' is fully supported by the 'Context'.
            Read the context carefully and then read the answer. Respond with only 'CORRECT' or 'INCORRECT'.

            Context:
            ---
            {context}
            ---
            Answer:
            ---
            {answer}
            ---
            """
            output=model_y_n.invoke(validation_prompt)
            if output.is_correct==True:
                logger.info("Answer validation passed")
                return answer
            else:
                logger.warning("Answer validation failed, retrying with new context")
                print('Making sure that the answer matches the context')
                new_docs=retriever.filter_documents(enhanced_query)
                new_context='\n\n'.join([doc.page_content for doc in new_docs])
                retry_prompt = f"""The previous answer was not supported by its context. Please try again.
                    Answer the following question based ONLY on the new, updated context provided.

                    Context:
                    {new_context}

                    Question: {enhanced_query}

                    Answer:
                    """
                new_answer = model.invoke(retry_prompt).content
                logger.info("Generated new answer with updated context")
                return new_answer

        except Exception as e:
                logger.error(f"Error during answer validation: {e}")
                print(f"An error occurred during validation: {e}")
                return answer # If validation fails, return the original answer

@tool(description='ingestes the report data into a vector store')
def ingest_data_filling(report_text: str, ticker: str):
    """
    Ingests the information of a company and stores it into a vector store for later retrieval.

    Args:
        report_text (str): The full text of the 10-K filing to be ingested.
        ticker (str): The stock ticker symbol of the company.

    Side Effects:
        - Creates a directory for the ticker under "INDEXED" if it does not exist.
        - Chunks the report text and generates embeddings.
        - Stores the embeddings in a persistent Chroma vector store.
        - Prints the path where vectors are saved.
        - Prints an error message if ingestion fails.
    """
    logger.info(f"Starting data ingestion for ticker: {ticker}")
    # Define the path where the indexed data will be stored
    path = Path("INDEXED") / ticker
    
    # Clean up any existing directory to avoid permission issues
    if path.exists():
        logger.info(f"Existing directory found at {path}, attempting to remove")
        try:
            # On macOS, we need to ensure we have proper permissions
            shutil.rmtree(path)
            logger.info(f"🧹 Removed existing directory: {path}")
            print(f"🧹 Removed existing directory: {path}")
        except Exception as e:
            logger.warning(f"Could not remove existing directory: {e}")
            print(f"⚠️ Could not remove existing directory: {e}")
            # Try to fix permissions
            try:
                os.system(f"chmod -R 755 {path}")
                shutil.rmtree(path)
                logger.info(f"🧹 Removed existing directory after fixing permissions: {path}")
                print(f"🧹 Removed existing directory after fixing permissions: {path}")
            except:
                logger.error(f"Failed to remove directory even after permission fix: {e}")
                return f"Error: Could not remove existing directory: {e}"
    
    try:
        # Create directory with proper permissions
        logger.info(f"Creating directory: {path}")
        path.mkdir(parents=True, exist_ok=True)
        
        # Set proper permissions on macOS
        os.system(f"chmod -R 755 {path}")
        
        # Split the report text into manageable chunks
        logger.info("Chunking report text")
        splits = better_chunking(report_text)
        # Create metadata chunks for each text chunk
        meta_data_chunks = chunk_metada(splits, ticker)
        
        # Initialize Google's embedding model
        logger.info("Initializing embeddings model")
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("google")
        )

        # Create vectorstore with error handling
        try:
            logger.info("Creating Chroma vector store")
            # Attempt to create Chroma vector store from documents
            vectorstore = Chroma.from_documents(
                meta_data_chunks, 
                embeddings, 
                persist_directory=str(path)
            )
            
            # Try to persist with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Persisting vector store (attempt {attempt+1})")
                    vectorstore.persist()
                    logger.info(f"✅ Vectors saved at: {path.resolve()}")
                    print(f"✅ Vectors saved at: {path.resolve()}")
                    break
                except Exception as persist_error:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to persist after {max_retries} attempts")
                        raise persist_error
                    logger.warning(f"Persist failed (attempt {attempt+1}), retrying...")
                    print(f"⚠️ Persist failed (attempt {attempt+1}), retrying...")
                    time.sleep(1)  # Wait before retrying
            
            logger.info(f"Successfully ingested 10-K for {ticker}")
            return f"Successfully ingested 10-K for {ticker}"
            
        except Exception as chroma_error:
            logger.warning("Chroma creation failed, trying fallback collection")
            # Fallback: try with a different collection name
            try:
                collection_name = f"{ticker}_{int(time.time())}"
                vectorstore = Chroma.from_documents(
                    meta_data_chunks, 
                    embeddings, 
                    persist_directory=str(path),
                    collection_name=collection_name
                )
                vectorstore.persist()
                logger.info(f"✅ Vectors saved with fallback collection: {path.resolve()}")
                print(f"✅ Vectors saved with fallback collection: {path.resolve()}")
                return f"Successfully ingested 10-K for {ticker} with fallback collection"
            except Exception as fallback_error:
                logger.warning("Fallback collection failed, trying permission fix")
                # Try to fix permissions and retry
                try:
                    os.system(f"chmod -R 755 {path}")
                    vectorstore.persist()
                    logger.info(f"✅ Vectors saved after fixing permissions: {path.resolve()}")
                    print(f"✅ Vectors saved after fixing permissions: {path.resolve()}")
                    return f"Successfully ingested 10-K for {ticker} after fixing permissions"
                except:
                    logger.error("All fallback attempts failed")
                    raise fallback_error

    except Exception as e:
        logger.error(f"Failed to create directory: {e}")
@tool(description='asks quesstion from the indexed vector store')
def query_data(ticker: str, query: str) -> str:
    """
    Queries the vector store for a given company's and returns an answer to the query.

    Args:
        ticker (str): The stock ticker symbol of the company to query.
        query (str): The user's question or query about the company.

    Returns:
        str: The answer generated by the model, or an error message if the query fails.

    Process:
        - Loads the vector store for the given ticker.
        - Creates a hybrid retriever (vector + BM25) if possible.
        - Enhances the user's query for better retrieval.
        - Retrieves relevant documents and creates a context with citations.
        - Formats a prompt for the model using the context and query.
        - Invokes the model to generate an answer.
        - Returns the model's answer or an error message.
    """
    logger.info(f"Processing query for ticker {ticker}")
    path = Path("INDEXED") / ticker
    if not path.exists():
        logger.warning(f"No vectorstore found for ticker {ticker}")
        return "There's no such vectorstore yet."

    try:
        logger.info("Initializing embeddings and vector store")
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("google")
        )
        vectorstore = Chroma(
            persist_directory=str(path),
            embedding_function=embeddings
        )

        logger.info("Creating hybrid retriever")
        retriever = create_hybrid_retreiver(vectorstore)

        logger.info("Enhancing query")
        enhanced = enhance_query(query,ticker)

        logger.info("Filtering documents")
        filtered_docs = retriever.filter_documents(enhanced)
        context = create_context_citations(filtered_docs)

        logger.info("Preparing prompt template")
        prompt = PromptTemplate(
            template=(
                "You are a senior and smart financial assistant. Use the following 10-K context "
                "to answer the question clearly and accurately.\n\n"
                "Context:\n{context}\n\n"
                "Question:\n{query}\n\n"
                "Answer with clear reasoning and cite sources."
            ),
            input_variables=["context", "query"],
        )

        final_prompt = prompt.format(context=context, query=query)

        logger.info("Generating answer")
        output = model.invoke(final_prompt)
        logger.info("Validating answer")
        new_output=answer_validator(enhanced_query=enhanced,answer=output.content,context=context,retriever=retriever)
        logger.info("Query processing completed successfully")
        return new_output
    except Exception as e:
        logger.error(f"Error during query processing: {e}")
        return f"An error occurred while querying the data: {e}"
