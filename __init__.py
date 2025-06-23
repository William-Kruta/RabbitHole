from modules.research.agents import ExplorerAgent
from modules.research.research import DeepResearch
from config.config import read_research_config


if __name__ == "__main__":

    research_config = read_research_config()
    dr = DeepResearch(research_config)

    dr.run_research("Find me the best IPOs to invest in")
