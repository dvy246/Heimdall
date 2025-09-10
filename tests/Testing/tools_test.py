import asyncio
from src.tools.technical_analysis import get_technical_analysis

def main():
    data = get_technical_analysis(ticker='MSFT')
    print(data)

if __name__ == "__main__":
    main()