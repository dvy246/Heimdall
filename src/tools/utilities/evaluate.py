from langchain_core.runnables import RunnableBranch, RunnablePassthrough
from langchain.prompts import PromptTemplate
from src.config.settings import model
from langchain.schema import StrOutputParser
from langchain_core.tools import tool

@tool(description='Evaluates and enhances professional financial reports')
def evaluate_report(report: str):
    """
    Evaluates and enhances financial reports for professional quality.
    
    Uses a two-stage process:
    1. Evaluation: Assesses report against professional standards (clarity, objectivity, etc.)
    2. Revision: If needed, improves the report while preserving key content
    
    Args:
        report (str): The financial report text to evaluate
        
    Returns:
        str: Either evaluation results (if PASS) or improved report (if FAIL)
    """
    eval_prompt = PromptTemplate(
        template="""You are a senior financial editor evaluating this report for professional quality.

Report:
{report}

Evaluate against these criteria with specific examples:
1. Clarity: Language precision and accessibility
2. Objectivity: Neutral tone and evidence-based statements
3. Completeness: Coverage of key financial areas
4. Logical Flow: Evidence-based conclusions
5. Professionalism: Executive-ready formatting and style

Provide:
- Detailed scoring (1-5) for each criterion
- Key strengths and areas for improvement
- Final grade: PASS or FAIL with justification""",
        input_variables=["report"]
    )
    
    revise_prompt = PromptTemplate(
        template="""As a senior financial editor, improve this report while maintaining its core content.

Original Report:
{report}

Requirements:
1. Maintain all key facts, findings and recommendations
2. Enhance clarity, structure and professional tone
3. Ensure precise, unambiguous language
4. Remove unsupported claims
5. Address any gaps in financial analysis
6. Optimize for executive/investor audience

Return only the revised report.""",
        input_variables=["report"]
    )

    eval_chain = eval_prompt | model | StrOutputParser()
    revise_chain = revise_prompt | model | StrOutputParser()

    def route(output: str) -> str:
        return "revise" if any(x in output.lower() for x in ['fail', 'needs improvement', 'needs revision']) else "pass"

    branch = RunnableBranch(
        (lambda x: route(x['evaluation_result']) == 'revise', revise_chain),
        RunnablePassthrough()
    )

    chain = {
        "report": RunnablePassthrough(),
        "evaluation_result": eval_chain
    } | branch
    
    return chain.invoke(report)