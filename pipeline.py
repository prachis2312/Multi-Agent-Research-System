from agents import build_reader_agent,build_search_agent,writer_chain,critic_chain
from rich import print
import re
from tools import scrape_url
from app import trim

def run_research_pipeline(topic: str)-> dict:
    state={}

    #Step-1 search agent
    print("\n"+" ="*50)
    print("step 1- search agent is working ...")
    print("="*50)

    search_agent=build_search_agent()
    search_result=search_agent.invoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {topic}. "
                      "For every key point, include the source URL.")]
    })
    state["search_results"]=search_result['messages'][-1].content
    print("\n search result ",state['search_results'])

    #step-2 reader agent
    print("\n"+" ="*50)
    print("step 2- reader agent will be scraping the urls given by reader agent...")
    print("="*50)

    

    urls = re.findall(r'https?://[^\s<>"\]]+', state["search_results"])
    reader_agent=build_reader_agent()
    reader_result=reader_agent.invoke({
        "messages": [
        ("user",
         f"Research topic: {topic}\n\n"
         f"Here are the URLs found during web search:\n"
         f"{urls}\n\n"
         "Choose the most relevant URL for this topic "
         "and use the scrape_url tool to retrieve its content.")
    ]
    })

    state['scraped_content']=reader_result['messages'][-1].content

    print("\nscraped content: \n",state['scraped_content'])


    #step 3- writer chain
    print("\n"+" ="*50)
    print("step 3- writer is drafting the report...")
    print("="*50)

    research_combined = (
    f"SEARCH RESULTS:\n{trim(state['search_results'], 3000)}\n\n"
    f"DETAILED SCRAPED CONTENT:\n{trim(state['scraped_content'], 6000)}"
    )

    state["report"]=writer_chain.invoke({
        "topic":topic,
        "research":research_combined
    })

    print("\n final report\n",state["report"])

    #step 4- Critic report
    print("\n"+" ="*50)
    print("step 4- critic is reviewing the report...")
    print("="*50)

    state["feedback"]=critic_chain.invoke({
        "report":state["report"]
    })

    print("\n critic report \n",state['feedback'])

    return state

if __name__=="__main__":
    topic=input("\nEnter a research topic: ")
    run_research_pipeline(topic)




