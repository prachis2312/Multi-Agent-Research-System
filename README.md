# Multi-Agent Research System

A research assistant built from four cooperating AI agents. Give it a topic and it searches the web, reads the most relevant source, writes a structured report, and then has a separate reviewer critique that report. A Streamlit interface shows what every agent did along the way.

**Live demo:** https://multi-agent-research-system-xughupzx9rrxk954ynqgbf.streamlit.app/

## How it works

| Step | Agent | What it does |
|------|-------|--------------|
| 1 | Search agent | Searches the web for recent, reliable information on the topic |
| 2 | Reader agent | Picks the most relevant link and scrapes its full content |
| 3 | Writer chain | Combines the search results and scraped content into a report |
| 4 | Critic chain | Reviews the report and gives feedback |

```
Topic -> Search agent -> Reader agent -> Writer -> Critic -> Report + Feedback
```

## Features

- Live progress for each of the four steps, with timings
- Report, reviewer feedback, source links and raw agent outputs in separate tabs
- Download the finished report as a Markdown file
- Session history in the sidebar to reopen earlier reports
- Command-line mode if you prefer the terminal

## Project structure

```
multi agent system/
├── app.py            # Streamlit UI
├── pipeline.py       # Pipeline logic (also runnable from the terminal)
├── agents.py         # Search agent, reader agent, writer and critic chains
├── tools.py          # Tools used by the agents (web search, URL scraping)
├── test_gemini.py    # Quick local test script
├── requirements.txt
└── .env              # API keys (not committed)
```

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/prachis2312/Multi-Agent-Research-System.git
cd Multi-Agent-Research-System
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Add your API keys

Create a `.env` file in the project root. Use the variable names that `agents.py` and `tools.py` read, for example:

```

GROQ_API_KEY=your-key-here
LINKUP_API_KEY=your-key-here
```

Never commit this file. It is listed in `.gitignore`.

### 4. Run the app

```bash
python -m streamlit run app.py
```

The app opens at `http://localhost:8501`.

To run without the UI:

```bash
python pipeline.py
```

## Deployment

The app is deployed on [Streamlit Community Cloud](https://streamlit.io/cloud) straight from this repository.

1. Push the project to GitHub (without `.env`).
2. On Streamlit Community Cloud, create a new app, select the repo, branch `main`, and main file `app.py`.
3. Under Advanced settings, choose Python 3.12 and add your API keys in the Secrets box in TOML format:
   ```toml
   GOOGLE_API_KEY = "your-key-here"
   GROQ_API_KEY = "your-key-here"
   TAVILY_API_KEY = "your-key-here"
   ```
4. Deploy. Every push to `main` redeploys automatically.

## Known limitations

- **Rate limits:** On free API tiers, large requests can fail with a token-per-minute error. The app trims long inputs before the writing step to stay within limits, which means very long sources are only partly used.
- **One source is read in full:** the reader agent scrapes a single page, so the report depends on that page plus the search summaries.
- **No persistent history:** past reports live in the browser session and disappear on refresh.
- **Public demo:** the hosted app uses the owner's API quota, so it may be slow or unavailable when limits are reached.

## Tech stack

- Python 3.12
- Streamlit
- LangChain and LangGraph (agents and chains)
- LLM providers: Groq and Google Gemini
- Web search and scraping tools

## License

Add a license of your choice, for example MIT.