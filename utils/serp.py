"""Search engine results page (SERP) utilities"""
import re
import datetime
import requests
from readability import Document
from duckduckgo_search import ddg

DEFAULT_SETTINGS = {
    "num_results": 3,
    "time_period": "",
    "region": "us",
}

def format_web_results(results: list) -> str:
    """Formats web results"""
    counter = 1
    return "\n".join([f"[{counter}] \"{result['body']}\"\nURL: {result['href']}\n\n" for result in results])


def get_serp(query: str, num_results: int, time_period: str, region: str) -> list:
    """Returns a list of search results"""

    serp_prompt = '''Web search results:

{web_results}
Current date: {current_date}

Instructions: Using the provided web search results, write a comprehensive reply to the given query. Make sure to cite results using [number](URL) notation after the reference. If the provided search results refer to multiple subjects with the same name, write separate answers for each subject.
Query: {query}'''

    web_results = api_search(query, num_results, time_period, region)
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")

    final = serp_prompt.format(
        web_results=format_web_results(web_results),
        current_date=current_date,
        query=query
    )

    return final

def normalize_text(text: str) -> str:
    """Normalizes text"""
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r"\s{3,}", " ", text)
    return text

def api_search(query: str, num_results: int, time_period: str, region: str) -> list:
    """Does a search using the DuckDuckGo API"""
    page_operator_matches = re.search(r"page:(\S+)", query)
    query_url = None

    if page_operator_matches:
	    # Not tested
        return;
        query_url = page_operator_matches.group(1)
        # Check is it is a valid URL
        if not re.match(r"^https?://", query_url):
            query_url = "http://" + query_url

        
    if query_url:
        result = page_to_text(query_url)
        return [{
            "title": result["title"],
            "body": result["body"],
            "href": query_url,
        }]
    else:
        output = []
        if time_period == "all":
            time_period = None
        results = ddg(query, region, safesearch='Off', time=time_period, max_results=num_results)
        print(results)
        for result in results:
            output.append({
                "title": result["title"],
                "body": result["body"],
                "href": result["href"],
            })
        return output

def page_to_text(url):
    """Converts a webpage to text"""
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    document = Document(response.text)
    # return title and summary
    return {
        "title": normalize_text(document.title()),
        "body": normalize_text(document.summary())
    }