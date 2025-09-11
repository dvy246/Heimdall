from src.config.looging_config import logger
import os
from agno.agent import Agent
from agno.knowledge.pdf import PDFKnowledgeBase, PDFReader
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.embedder.cohere import CohereEmbedder
from agno.vectordb.chroma import ChromaDb
from agno.team import Team
from langchain_core.tools import tool
from src.config.settings import model2


logger.info('compliance agent started')
@tool(description='This tool uses its knowledge to ensure regulations and guidelines for a good report.')
def create_compliance_team(query: str) -> str:
    """
    Creates and runs a regulatory compliance team to analyze a query against SEC, SEBI, and CFA knowledge bases.

    Args:
        query (str): The query to be analyzed by the compliance team.

    Returns:
        str: The compliance report or an error message.

    Raises:
        FileNotFoundError: If any of the required PDF documents are not found.
        ValueError: If the COHERE_API_KEY is not set in the environment variables.
    """
    logger.info(f"Creating compliance team for query: {query}")

    cohere_api_key = os.getenv("COHERE_API_KEY")
    if not cohere_api_key:
        raise ValueError("COHERE_API_KEY is not set in environment variables.")

    base_path = '/Users/divyyadav/Desktop/Heimdall/src/knowledge_base/'
    paths: Dict[str, str] = {
        'SEC_REGULATIONS': os.path.join(base_path, 'sec_regulations.pdf'),
        'SEBI_REGULATIONS': os.path.join(base_path, 'sebi.pdf'),
        'CFA_GUIDELINES': os.path.join(base_path, 'rc-equity-research-report-essentials.pdf'),
        'CFA_COE_GUIDELINES': os.path.join(base_path, 'code-of-ethics-standards-professional-conduct.pdf')
    }

    for name, path in paths.items():
        if not os.path.exists(path):
            logger.error(f"{name} file not found at: {path}")
            raise FileNotFoundError(f"{name} file not found at: {path}")

    data_path = os.path.join(base_path, 'data')
    os.makedirs(data_path, exist_ok=True)

    def make_pdf(dbname: str, path: str, collection_name: str) -> PDFKnowledgeBase:
        return PDFKnowledgeBase(
            path=path,
            vector_db=ChromaDb(
                collection=collection_name,
                embedder=CohereEmbedder(api_key=cohere_api_key, id="embed-english-v3.0"),
                persistent_client=True,
                path=os.path.join(data_path, dbname)
            ),
            reader=PDFReader(chunk=True)
        )

    try:
        sec_kb = make_pdf(collection_name="SEC", path=paths["SEC_REGULATIONS"], dbname='sec')
        cfa_kb = make_pdf(collection_name="CFA", path=paths["CFA_GUIDELINES"], dbname='cfa')
        sebi_kb = make_pdf(collection_name="SEBI", path=paths["SEBI_REGULATIONS"], dbname='sebi')
        cfa_coe = make_pdf(collection_name="CFA_RULES", path=paths["CFA_COE_GUIDELINES"], dbname='cfa_coe')

        combined_knowledge = CombinedKnowledgeBase(
            sources=[sec_kb, sebi_kb, cfa_coe],
            vector_db=ChromaDb(
                collection="combined_regulatory",
                embedder=CohereEmbedder(api_key=cohere_api_key, id="embed-english-v3.0"),
                persistent_client=True,
                path=os.path.join(data_path, "combined_chromadb")
            )
        )
        
        agent = Agent(
            knowledge=combined_knowledge,
            search_knowledge=True,
            model=model2,
            instructions="You are a helpful regulatory assistant with knowledge about SEC and SEBI oversight."
        )

        agent2 = Agent(
            model=model2,
            knowledge=cfa_kb,
            search_knowledge=True,
            instructions="You are a helpful assistant with knowledge about CFA guidelines and equity research."
        )

        team = Team(
            [agent, agent2],
            model=model2,
            name='regulator',
            mode="coordinate",
            instructions="""You are a team coordinator. First, consult the regulatory assistant to check compliance with SEC and SEBI regulations. Then, consult the CFA guidelines assistant to verify adherence to CFA equity research standards. Synthesize findings from both agents to provide comprehensive guidance."""
        )

        response = team.run(query)
        report = str(response.content) if hasattr(response, 'content') else str(response)
        logger.info("Compliance team execution completed successfully.")
        return report

    except Exception as e:
        logger.error(f"An error occurred during compliance team execution: {e}", exc_info=True)
        return f"Error: An unexpected error occurred during compliance analysis. Please check the logs for more details."