import os
import asyncio
import aiohttp
import json
import re
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from src.config.settings import model
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class SecFilingData(BaseModel):
    ticker: str = Field(description='The company ticker symbol')
    filing_type: str = Field(description='The type of SEC filing (e.g., 10-K, 10-Q)')
    filing_date: str = Field(description='The filing date')
    filing_url: str = Field(description='URL to the filing document')

class SecEdgarFetcher:
    def __init__(self):
        self.__user_agent = {"User-Agent": "your.email@example.com"}
        self.__baseurl = "https://data.sec.gov"
        self._cik_cache = {}

    async def _simple_cik(self, ticker: str):
        """Get CIK for a ticker symbol"""
        # Check cache first
        if ticker.upper() in self._cik_cache:
            return self._cik_cache[ticker.upper()]

        headers = self.__user_agent
        try:
            url = "https://www.sec.gov/files/company_tickers.json"

            # Use a single session with proper timeout and connector limits
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)

            async with aiohttp.ClientSession(
                headers=headers,
                timeout=timeout,
                connector=connector
            ) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()

                cik = None
                # Find CIK for ticker
                for record in data.values():
                    if record.get("ticker", "").upper() == ticker.upper():
                        cik = str(record.get("cik_str", "")).zfill(10)
                        break

                if cik:
                    print(f"Found CIK for {ticker}: {cik}")
                    # Cache the result
                    self._cik_cache[ticker.upper()] = cik
                    return cik
                else:
                    print(f"CIK not found for {ticker}")
                    return None

        except Exception as e:
            print(f"Error getting CIK for {ticker}: {e}")
            return None

    async def _fetch_with_session(self, session, url):
        """Fetch URL content using provided session"""
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    async def _fetch_filing_items(self, ticker: str, filing_type: str = "10-K", limit: int = 1):
        """Fetch filing items for a specific ticker and filing type"""
        # Get CIK first (this will cache it)
        cik = await self._simple_cik(ticker)
        if not cik:
            return []

        # Use a single session for all requests
        timeout = aiohttp.ClientTimeout(total=60)  # Longer timeout for large filings
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=3)

        try:
            async with aiohttp.ClientSession(
                headers=self.__user_agent,
                timeout=timeout,
                connector=connector
            ) as session:
                # Get submissions data
                url = f"{self.__baseurl}/submissions/CIK{cik}.json"
                submissions_data = await self._fetch_with_session(session, url)

                if not submissions_data:
                    return []

                submissions = json.loads(submissions_data)
                filings = submissions.get("filings", {}).get("recent", {})

                result = []
                forms = filings.get("form", [])
                accession_numbers = filings.get("accessionNumber", [])
                primary_documents = filings.get("primaryDocument", [])
                filing_dates = filings.get("filingDate", [])

                for i, form in enumerate(forms):
                    if form == filing_type and len(result) < limit:
                        try:
                            accession = accession_numbers[i].replace("-", "")
                            filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{primary_documents[i]}"

                            print(f"Fetching {filing_type} from {filing_dates[i]}...")

                            # Add delay between requests to be respectful
                            if i > 0:
                                await asyncio.sleep(0.5)

                            html = await self._fetch_with_session(session, filing_url)
                            if not html:
                                continue

                            # Parse HTML and extract items
                            soup = BeautifulSoup(html, "html.parser")

                            # Remove script and style elements
                            for script in soup(["script", "style"]):
                                script.decompose()

                            text = soup.get_text(" ", strip=True)
                            # Normalize whitespace
                            text = re.sub(r'\s+', ' ', text)

                            # Find all Item headers with improved regex
                            item_pattern = r'(?:^|\s)(Item\s+\d+[A-Za-z]?(?:\.[A-Za-z])?\.?\s*[—\-–]?\s*[^\n]*?)(?=\s+Item\s+\d+|\s+ITEM\s+\d+|$)'
                            matches = list(re.finditer(item_pattern, text, re.IGNORECASE | re.MULTILINE))

                            items = []
                            for j in range(len(matches)):
                                start = matches[j].start()
                                end = matches[j+1].start() if j+1 < len(matches) else len(text)
                                item_text = text[start:end].strip()

                                # Limit item length to avoid huge text blocks
                                if len(item_text) > 10000:
                                    item_text = item_text[:10000] + "... [truncated]"

                                items.append(item_text)

                            result.append({
                                "ticker": ticker,
                                "filing_type": filing_type,
                                "filing_date": filing_dates[i],
                                "filing_url": filing_url,
                                "accession_number": accession_numbers[i],
                                "items": items,
                                "total_items": len(items)
                            })

                            print(f"✅ Extracted {len(items)} items from {filing_type}")

                        except Exception as e:
                            print(f"Error processing filing {i}: {e}")
                            continue

                return result

        except Exception as e:
            print(f"Error in fetch_filing_items: {e}")
            return []
    async def _fetch_sec_company_data(self, ticker: str, filing_type: str = "10-K", limit: int = 5):
        """Fetch essential company data from SEC EDGAR"""
        cik = await self._simple_cik(ticker)

        if not cik:
            raise ValueError(f"Could not find CIK for {ticker}")

        async with aiohttp.ClientSession(headers=self.__user_agent) as session:
            # ---- 1. Company Profile & Filings Metadata ----
            async with session.get(f"{self.__baseurl}/submissions/CIK{cik}.json") as resp:
                profile_data = await resp.json()

            company_info = {
                "cik": profile_data.get("cik"),
                "name": profile_data.get("name"),
                "tickers": profile_data.get("tickers"),
                "exchanges": profile_data.get("exchanges"),
                "sicDescription": profile_data.get("sicDescription"),
                "fiscalYearEnd": profile_data.get("fiscalYearEnd"),
                "website": profile_data.get("website"),
            }

            filings = []
            recent = profile_data.get("filings", {}).get("recent", {})
            for idx, form in enumerate(recent.get("form", [])):
                if form == filing_type and len(filings) < limit:
                    filings.append({
                        "accessionNumber": recent["accessionNumber"][idx],
                        "form": form,
                        "reportDate": recent["reportDate"][idx],
                        "filingDate": recent["filingDate"][idx],
                    })

            # ---- 2. Financial Facts (Key Line Items) ----
            async with session.get(f"{self.__baseurl}/api/xbrl/companyfacts/CIK{cik}.json") as resp:
                facts_data = await resp.json()

            us_gaap = facts_data.get("facts", {}).get("us-gaap", {})
            dei = facts_data.get("facts", {}).get("dei", {})

            def safe_get(source, key):
                """Helper to safely extract most recent value for a fact."""
                if key in source:
                    units = source[key].get("units", {})
                    for _, vals in units.items():
                        if vals:
                            return vals[-1]  # latest
                return None

            # Core financials
            financials = {
                "Assets": safe_get(us_gaap, "Assets"),
                "Liabilities": safe_get(us_gaap, "Liabilities"),
                "Revenues": safe_get(us_gaap, "Revenues"),
                "NetIncomeLoss": safe_get(us_gaap, "NetIncomeLoss"),
                "EarningsPerShareBasic": safe_get(us_gaap, "EarningsPerShareBasic"),
                "CashAndCashEquivalents": safe_get(us_gaap, "CashAndCashEquivalentsAtCarryingValue"),
                "StockholdersEquity": safe_get(us_gaap, "StockholdersEquity"),
                "SharesOutstanding": safe_get(dei, "EntityCommonStockSharesOutstanding"),
            }

            # ---- 3. Ratios ----
            try:
                assets = financials["Assets"]["val"] if financials["Assets"] else None
                liabilities = financials["Liabilities"]["val"] if financials["Liabilities"] else None
                revenues = financials["Revenues"]["val"] if financials["Revenues"] else None
                net_income = financials["NetIncomeLoss"]["val"] if financials["NetIncomeLoss"] else None
                equity = financials["StockholdersEquity"]["val"] if financials["StockholdersEquity"] else None
            except (TypeError, KeyError):
                assets = liabilities = revenues = net_income = equity = None

            ratios = {
                "DebtToEquity": (liabilities / equity) if liabilities and equity else None,
                "ProfitMargin": (net_income / revenues) if net_income and revenues else None,
                "CurrentRatio": (assets / liabilities) if assets and liabilities else None,
            }

        return {
            "company_info": company_info,
            "recent_filings": filings,
            "financials": financials,
            "ratios": ratios,
        }

sec_edgar_fetcher = SecEdgarFetcher()

def run_async_safely(coro):
    """
    Safely run async code in a synchronous context.

    This function attempts to run an async coroutine from a synchronous context.
    If already inside a running event loop (e.g., in a Jupyter notebook), it uses
    nest_asyncio to allow nested event loops. Otherwise, it creates a new event loop.

    Args:
        coro: The coroutine to run.

    Returns:
        The result of the coroutine.
    """
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running event loop
            return asyncio.run(coro)
        else:
            # Already running in an event loop (e.g., Jupyter)
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
    except Exception as e:
        raise RuntimeError(f"Failed to run async coroutine: {e}")

@tool(description="""
Extracts key sections from SEC filings for a company, including business description, risk factors, MD&A, and financial statements.

Args:
- ticker (string): Company ticker symbol (e.g., 'AAPL', 'MSFT', 'TSLA')
- filing_types (list): List of filing types to extract from (e.g., ['10-K', '10-Q'])
- limit_per_type (int): Number of filings per type to process (default: 1)

Example call:
extract_key_sections(ticker='AAPL', filing_types=['10-K', '10-Q'], limit_per_type=1)
""")
def extract_key_sections(ticker: str, filing_types: List[str] = None, limit_per_type: int = 1) -> dict:
    """
    Extracts key sections from SEC filings for a company.
    """
    print('extracting sections baby')
    if filing_types is None:
        filing_types = ["10-K", "10-Q"]
    
    async def extract_sections():
        all_filings = []
        for filing_type in filing_types:
            filings = await sec_edgar_fetcher._fetch_filing_items(ticker.upper(), filing_type, limit_per_type)
            all_filings.extend(filings)
        
        extracted_data = []
        FILING_ITEM_MAPPINGS = {
            "10-K": {
                "business": ["Item 1", "Item 1."],
                "risk_factors": ["Item 1A", "Item 1A."],
                "md_a": ["Item 7", "Item 7."],
                "financial_statements": ["Item 8", "Item 8."],
            },
            "10-Q": {
                "financial_statements": ["Item 1", "Item 1."],
                "md_a": ["Item 2", "Item 2."],
                "controls": ["Item 4", "Item 4."],
            },
        }
        
        for filing in all_filings:
            filing_type = filing["filing_type"]
            target_items = FILING_ITEM_MAPPINGS.get(filing_type, {})
            key_sections = {}
            
            for item_content in filing.get("items", []):
                item_header = item_content[:100].lower()
                
                for section_name, potential_headers in target_items.items():
                    if section_name in key_sections:
                        continue
                    
                    for header_text in potential_headers:
                        if header_text.lower() in item_header:
                            key_sections[section_name] = item_content
                            break
            
            extracted_data.append({
                "ticker": ticker,
                "filing_type": filing_type,
                "filing_date": filing["filing_date"],
                "sections": key_sections,
            })
        
        return {"ticker": ticker, "extracted_sections": extracted_data}
    
    return run_async_safely(extract_sections())

@tool(description="""
Fetches SEC filing data for a company including 10-K, 10-Q, and other filings.

Args:
- ticker (string): Company ticker symbol (e.g., 'AAPL', 'MSFT', 'TSLA')
- filing_type (string): Type of filing (e.g., '10-K', '10-Q', '8-K')
- limit (int): Number of recent filings to fetch (default: 1)

Example call:
fetch_sec_filings(ticker='AAPL', filing_type='10-K', limit=1)
""")
def fetch_sec_filings(ticker: str, filing_type: str = "10-K", limit: int = 1) -> dict:
    """
    Fetches SEC filing data for a specific company.

    Args:
        ticker: The company's stock ticker symbol
        filing_type: The type of SEC filing to fetch (e.g., '10-K', '10-Q', '8-K')
        limit: Number of recent filings to fetch

    Returns:
        Dictionary containing the filing data from SEC EDGAR
    """
    return run_async_safely(
        sec_edgar_fetcher._fetch_filing_items(ticker.upper(), filing_type, limit)
    )

@tool(description="""
Fetches comprehensive company data from SEC EDGAR including financials and ratios.

Args:
- ticker (string): Company ticker symbol (e.g., 'AAPL', 'MSFT', 'TSLA')
- filing_type (string): Type of filing to focus on (e.g., '10-K', '10-Q')
- limit (int): Number of recent filings to include (default: 5)

Example call:
fetch_sec_company_data(ticker='AAPL', filing_type='10-K', limit=5)
""")
def fetch_sec_company_data(ticker: str, filing_type: str = "10-K", limit: int = 5) -> dict:
    """
    Fetches comprehensive company data from SEC EDGAR.

    Args:
        ticker: The company's stock ticker symbol
        filing_type: The type of filing to focus on
        limit: Number of recent filings to include

    Returns:
        Dictionary containing company info, financials, and ratios
    """
    return run_async_safely(
        sec_edgar_fetcher._fetch_sec_company_data(ticker.upper(), filing_type, limit)
    )

@tool(description="""
Fetches multiple types of SEC filings for a company.

Args:
- ticker (string): Company ticker symbol (e.g., 'AAPL', 'MSFT', 'TSLA')
- filing_types (list): List of filing types (e.g., ['10-K', '10-Q', '8-K'])
- limit_per_type (int): Number of filings per type (default: 1)

Example call:
fetch_multiple_sec_filings(ticker='AAPL', filing_types=['10-K', '10-Q'], limit_per_type=1)
""")
def fetch_multiple_sec_filings(ticker: str, filing_types: List[str] = None, limit_per_type: int = 1) -> dict:
    """
    Fetches multiple types of SEC filings for a company.

    Args:
        ticker: The company's stock ticker symbol
        filing_types: List of filing types to fetch
        limit_per_type: Number of filings per type

    Returns:
        Dictionary containing all requested filings
    """
    if filing_types is None:
        filing_types = ["10-K", "10-Q", "8-K"]
    
    async def fetch_all():
        all_filings = []
        for filing_type in filing_types:
            print(f"\n�� Fetching {filing_type} filings for {ticker}...")
            filings = await sec_edgar_fetcher._fetch_filing_items(ticker.upper(), filing_type, limit_per_type)
            all_filings.extend(filings)
            # Small delay between different filing types
            await asyncio.sleep(1)
        return {"ticker": ticker, "filings": all_filings, "total_filings": len(all_filings)}
    
    return run_async_safely(fetch_all())

# Update the agent with this new, detailed prompt
sec_edgar_agent = create_react_agent(
    model=model,
    tools=[fetch_sec_filings, fetch_sec_company_data, fetch_multiple_sec_filings, extract_key_sections],
    name='sec_edgar_agent',
    prompt=(
        "You are a top-tier financial analyst. Your task is to generate a DEEP, COMPREHENSIVE due diligence report on a public company using SEC EDGAR data. "
        "Your report must be based SOLELY on data fetched by the tools provided. DO NOT HALLUCINATE or use prior knowledge.\n\n"
        "**MANDATORY EXECUTION PLAN:** You MUST follow these steps in order for a complete analysis:\n"
        "1.  **COMPANY OVERVIEW:** First, use the 'fetch_sec_company_data' tool to get the company's identity, core financial facts, and calculated ratios.\n"
        "2.  **KEY NARRATIVE SECTIONS:** Second, use the 'extract_key_sections' tool on the latest '10-K' to get the qualitative story: Business Description, Risk Factors, and Management's Discussion (MD&A).\n"
        "3.  **DETAILED FILING DATA (If needed):** If the user asks for very specific details from a filing, use 'fetch_sec_filings' or 'fetch_multiple_sec_filings'.\n\n"
        "**ANALYSIS REQUIREMENTS:** After gathering all data, your final report MUST include the following sections:\n"
        "   a.  **Executive Summary:** A high-level overview of the company's health and performance.\n"
        "   b.  **Business Model & Strategy:** Summarize the 'business' section from the 10-K. What does the company do? What is its strategy?\n"
        "   c.  **Financial Health Analysis:** Present the data from 'fetch_sec_company_data'. Analyze the ratios (Profit Margin, Debt-to-Equity, etc.). What are the trends? What are the strengths and red flags?\n"
        "   d.  **Risk Assessment:** Summarize and analyze the key 'risk_factors' from the 10-K. What are the biggest threats to this business?\n"
        "   e.  **Management's Perspective:** Summarize the key points from the 'md_a' section. How does management explain the financial results and future outlook?\n"
        "   f.  **Investment Conclusion:** Synthesize the quantitative data and qualitative narratives into a final verdict. Is the company stable, growing, or risky? Support your conclusion with evidence from the fetched data.\n\n"
        "**CRITICAL FORMATTING RULE:** Present numerical data clearly. When mentioning a figure (e.g., Revenue, Net Income), always put it in **bold** like **$123.5M** for clarity.\n\n"
        "Example of a good analysis step: 'The company's Debt-to-Equity ratio is **0.85**, which indicates a moderate level of leverage and is common for the industry.'"
    )
)

import asyncio

agent_query = """
Generate a comprehensive due diligence report for google. 
Perform a deep analysis and provide your final report with the required sections: Executive Summary, Business Model, Financial Health, Risk Assessment, Management's Perspective, and Investment Conclusion.
Ensure all numerical data is presented in bold. extract 10-K and 10-Q and 8-K filings for google. and also extract its key sections using ur tool
"""

async def comprehensive_analysis():
    agent_result = await sec_edgar_agent.ainvoke({
        'messages': [HumanMessage(content=agent_query)]
    })
    return agent_result

# Run it
result = run_async_safely(comprehensive_analysis())
print(result['messages'][-1].content)