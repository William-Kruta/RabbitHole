import os
import json
import time
import logging
import requests


from modules.research.tools import (
    clean_text,
    clean_multiple_texts,
    fetch_page_content,
    recommend_web_sources,
    refine_prompt_for_web,
    search_google,
)
from modules.research.agents import (
    AnalystAgent,
    CriticAgent,
    ExplorerAgent,
    SynthesizerAgent,
    WebSearcher,
)

from config.config import get_research_output_path

# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )
# logger = logging.getLogger("ollama")  # Or the specific module within 'ollama'

# # Set the logging level to WARNING or higher
# logger.setLevel(logging.WARNING)
# logger = logging.getLogger("requests")  # Or the specific module within 'ollama'

# # Set the logging level to WARNING or higher
# logger.setLevel(logging.WARNING)


class DeepResearch:
    def __init__(self, research_config: dict, show_progress: bool = True):
        self.config = research_config
        self.analyst = AnalystAgent(self.config["analyst"]["model"])
        self.critic = CriticAgent(self.config["critic"]["model"])
        self.explorer = ExplorerAgent(self.config["explorer"]["model"])
        self.synthesizer = SynthesizerAgent(self.config["synthesizer"]["model"])
        self.web_searcher = WebSearcher(self.config["web_searcher"]["model"])
        self.current_depth = 0
        self.show_progress = show_progress
        self.history = []
        self.short_term_memory = []
        self.long_term_memory = []

    def run_research(self, topic: str, recursion_depth: int = 3):
        """Public-facing method to start the recursive research process."""
        print(
            f"--- Starting Recursive Research for topic: '{topic}' with depth: {recursion_depth} ---"
        )
        self.origin_topic = topic
        connected = self.analyst.model.check_connection()
        print(f"Connected: {connected}")

        if not connected:
            raise requests.ConnectionError

        research_results = self._recursive_step(
            current_topic=topic,
            recursion_depth=recursion_depth,
            research_history=[],
        )
        path = "output\\{}.json"
        file_name = self._create_file_name(topic, self.explorer)
        file_name = self.generate_unique_filename(file_name)
        self._save_research(research_results, path.format(file_name))

    def _save_research(self, research_results: list, path: str):
        print("Saving results to JSON...")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(research_results, f, ensure_ascii=False, indent=4)
        print("Saved to {}".format(path))

    def _create_file_name(self, topic: str, agent):
        output_dir = get_research_output_path()
        files = os.listdir(output_dir)

        prompt = f"""Based on this topic: '{topic}', create a file name. Respond with nothing but the file name. Avoid spaces, use '_' instead. DO NOT include file extensions. For reference here are the current files: {files}. Do not repeat file names, but they can be similar. """
        response = agent.model.get_response(prompt)
        return response

    def _recursive_step(
        self,
        current_topic: str,
        recursion_depth: int,
        research_history: list,
    ):
        label = self.current_depth + 1
        if self.current_depth >= recursion_depth:
            print(
                "--- Reached maximum recursion depth. Returning research history. ---"
            )
            return research_history

        start = time.time()
        print("================================\n")
        if self.show_progress:
            print(f"[{label}.1] Current Topic: {current_topic}")
        # sources = recommend_web_sources(current_topic, self.explorer)

        web_query = refine_prompt_for_web(current_topic, self.web_searcher)
        urls = search_google(web_query)
        web_content = []
        sources = []
        for u in urls:
            content = fetch_page_content(u)
            content = clean_text(content)
            if content != "":
                sources.append(u)
                web_content.append(content)
        ### Analysis
        if self.show_progress:
            print(f"[{label}.2] Analyzing content...")
        if self.current_depth > 0:
            current_topic = (
                f"Origin Topic: {self.origin_topic} | Current Topic: {current_topic}"
            )

        analysis = self._analyze(
            current_topic,
            web_content,
            self.analyst,
            self.config["analyst"]["context_window"],
        )
        ### Criticism
        if self.show_progress:
            print(f"[{label}.3] Critisizing analysis...")
        if self.current_depth > 0:
            analysis = (
                f"Origin Topic: {self.origin_topic} | Current Analysis: {analysis}"
            )
        criticism = self._critisize(
            analysis, web_content, self.critic, self.config["critic"]["context_window"]
        )
        ### Synthesize
        if self.show_progress:
            print(f"[{label}.4] Synthesizing responses...")
        synthesized = self._synthesize(
            analysis,
            criticism,
            self.synthesizer,
            self.config["synthesizer"]["context_window"],
        )
        ### Explore
        if self.show_progress:
            print(f"[{label}.5] Exploring topic further...")
        next_step = self._next_step(
            synthesized, self.explorer, self.config["explorer"]["context_window"]
        )
        end = time.time()
        elapse = end - start
        research_state = {
            "depth": self.current_depth,
            "topic": current_topic,
            "web_query": web_query,
            "analysis": analysis,
            "critique": criticism,
            "synthesis": synthesized,
            "sources": sources,
            "next_question": next_step,
            "elapse": elapse,
        }
        research_history.append(research_state)
        self.current_depth += 1
        return self._recursive_step(
            current_topic=next_step,
            recursion_depth=recursion_depth,
            research_history=research_history,
        )

    def _analyze(self, topic: str, context: list, agent, context_window: int):
        if self.current_depth > 0:
            prompt = f"Origin Topic: {self.origin_topic}. Use these web search results to answer this question: {topic}. Here are the results: {context}"
        else:
            prompt = f"Use these web search results to answer this question: {topic}. Here are the results: {context}"

        response = agent.model.get_response(prompt, context_window=context_window)
        return response

    def _critisize(
        self, analysis: str, context: list, agent, context_window: int
    ) -> str:
        if self.current_depth > 0:
            prompt = f"""Origin Topic: {self.origin_topic} Critically evaluate the following analysis. Identify any potential biases,
                        unstated assumptions, or logical fallacies. Is the evidence strong enough
                        to support the conclusions?

                        --- ANALYSIS ---
                        {analysis}

                        --- SOURCES --- 
                        {context}
                        """
        else:
            prompt = f"""Critically evaluate the following analysis. Identify any potential biases,
                    unstated assumptions, or logical fallacies. Is the evidence strong enough
                    to support the conclusions?

                    --- ANALYSIS ---
                    {analysis}

                    --- SOURCES --- 
                    {context}
                    """

        response = agent.model.get_response(prompt, context_window=context_window)
        return response

    def _synthesize(self, analysis: str, criticism: str, agent, context_window: int):
        prompt = f"""Create a coherent summary that incorporates the initial analysis and the subsequent critique.
                    Present a balanced view based on both pieces of information.

                    --- INITIAL ANALYSIS ---
                    {analysis}

                    --- CRITIQUE ---
                    {criticism}
                    """
        response = agent.model.get_response(prompt, context_window=context_window)
        return response

    def _next_step(self, synthesis: str, agent, context_window: int) -> str:

        prompt = f"""
            Based on the following research summary and critique, what are the most
            important unanswered questions or next steps for a deeper investigation? Determine the most important details and create a question. Respond with only the question you create. 

            --- SUMMARY ---
            {synthesis}
            
            STAY ON TOPIC WITH THE ORIGIN TOPIC: {self.origin_topic}                
            """

        response = agent.model.get_response(prompt, context_window=context_window)
        return response

    def generate_unique_filename(self, filename):
        """
        Generates a unique filename by appending a counter to the base filename if it already exists.

        Args:
            filename (str): The base filename.

        Returns:
            str: A unique filename.
        """
        base, ext = os.path.splitext(filename)
        counter = 1

        while os.path.exists(filename):
            filename = f"{base}_{counter}{ext}"
            counter += 1

        return filename
