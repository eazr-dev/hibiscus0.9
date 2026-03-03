from langchain_community.tools import DuckDuckGoSearchRun



def get_live_event_data(query: str) -> str:

    search_tool = DuckDuckGoSearchRun()
    results = search_tool.invoke(query)
    print(results)
    return results