import os
import requests
from langchain.tools import tool
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from linkup import LinkupClient
from rich import print

load_dotenv()
client=LinkupClient(
    api_key=os.getenv("LINKUP_API_KEY")
)

@tool
def web_search(query: str)-> str:
    """Search the web for recent and reliable information on a topic.Returns Title, URLs and snippets"""
    results=client.search(query=query,depth="standard",output_type="searchResults",include_images=False)

    out=[]
    for r in results.results[:5]:
        out.append(
            f"Title: {r.name}\nURL: {r.url}\nSnippet: {r.content[:300]}\n"
        )

    return "\n-----\n".join(out)

@tool
def scrape_url(url:str)-> str:
    """Scrape and return clean text content from a given URL for deeper reading"""
    try:
        resp=requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0"})
        soup=BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script","style","nav","footer"]):
            tag.decompose()
        return soup.get_text(separator=" ",strip=True)[:3000]
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"


#print(scrape_url.invoke("https://www.designtechguide.com/analysis/what-is-aesthetics"))
# print(web_search.invoke("what is the recent news of war?"))



