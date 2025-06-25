import re
import time
from typing import List, Tuple
import datetime as dt
from config.config import read_settings
from modules.research.actions import analyze, critisize, next_step, synthesize
from modules.research.agents import (
    AnalystAgent,
    CriticAgent,
    ExplorerAgent,
    SynthesizerAgent,
)

from modules.research.tools import (
    search_google,
    fetch_page_content,
    clean_multiple_texts,
)


class DeepResearch:
    def __init__(self, status_callback=None):
        self.settings = read_settings()
        self.analyst = AnalystAgent(self.settings["model"]["analyst"]["model_name"])
        self.critic = CriticAgent(self.settings["model"]["critic"]["model_name"])
        self.explorer = ExplorerAgent(self.settings["model"]["explorer"]["model_name"])
        self.synthesizer = SynthesizerAgent(
            self.settings["model"]["synthesizer"]["model_name"]
        )
        self.step_str = ""
        self.report = ""
        self.all_research = []
        self.status_callback = status_callback
        self.user_feedback = None

    def set_user_feedback(self, feedback):
        """Stores feedback from the user to influence the next step."""
        self.user_feedback = feedback

    def set_step_str(self, text: str, current_step: int, max_steps: int):
        """Sets the step string and calls the callback to update the GUI."""
        self.step_str = text
        if self.status_callback:
            self.status_callback((text, current_step, max_steps))

    def start_research(
        self, topic: str, research_iterations: int = 3, web_iterations: int = 5
    ):
        self.origin_topic = topic
        self.current_topic = topic
        index = 0
        current_step = 0
        num_operations = 5  # web, analyze, critisize, synthesize, explore
        max_steps = research_iterations * num_operations
        for i in range(research_iterations):
            start = time.time()
            current_step += 1
            index_str = index + 1
            self.set_step_str(
                f"====================\n[{index_str}.0] Topic: {self.current_topic}",
                current_step,
                max_steps,
            )
            self.set_step_str(
                f"[{index_str}.1] Searching the web...",
                current_step,
                max_steps,
            )
            refined_web_prompt = self.refine_query_for_web(self.current_topic)
            urls = search_google(refined_web_prompt, num_results=web_iterations)
            content = []
            for u in urls:
                c = fetch_page_content(u)
                content.append(c)

            content = clean_multiple_texts(content)
            content = "\n".join(content)
            # Analysis
            current_step += 1
            self.set_step_str(
                f"[{index_str}.2] Analyzing data...", current_step, max_steps
            )
            analysis = analyze(
                self.current_topic,
                content,
                self.analyst,
                self.settings["model"]["analyst"]["context_window"],
            )
            # Critisize
            current_step += 1
            self.set_step_str(
                f"[{index_str}.3] Critisizing analysis...", current_step, max_steps
            )
            criticism = critisize(
                analysis,
                content,
                self.critic,
                self.settings["model"]["critic"]["context_window"],
            )
            # Synthesize
            current_step += 1
            self.set_step_str(
                f"[{index_str}.4] Synthesizing responses...", current_step, max_steps
            )
            synthesis = synthesize(
                analysis,
                criticism,
                self.synthesizer,
                self.settings["model"]["synthesizer"]["context_window"],
            )
            # Explore
            current_step += 1
            self.set_step_str(
                f"[{index_str}.5] Generating next question...", current_step, max_steps
            )
            next_question = next_step(
                synthesis,
                self.origin_topic,
                self.explorer,
                self.settings["model"]["explorer"]["context_window"],
            )
            end = time.time()
            elapse = end - start
            r = {
                "topic": self.current_topic,
                "web_query": refined_web_prompt,
                "sources": urls,
                "analysis": analysis,
                "criticism": criticism,
                "synthesis": synthesis,
                "next_question": next_question,
                "elapse": elapse,
            }
            if self.user_feedback:
                self.set_step_str(f"Incorporating user feedback: {self.user_feedback}")
                self.current_topic = (
                    f"{self.user_feedback} - based on this, explore: {next_question}"
                )
                self.user_feedback = None
            else:
                self.current_topic = next_question

            index += 1

            self.all_research.append(r)

        self.report = self.generate_report(self.origin_topic, self.analyst)
        self.set_step_str(
            f"\nResearch complete for topic: '{self.origin_topic}'!",
            max_steps,
            max_steps,
        )

    def get_report(self):
        return self.report

    def refine_query_for_web(self, query: str):
        prompt = f"Take this user's query and refine it to be a web search. Here is the current date if relevant: {dt.datetime.now().date()}\nHere is the user's query: {query}. Return nothing but the refined query. Stick close to the original query. Do not add extra questions."
        return self.explorer.model.get_response(prompt)

    def generate_report(self, origin_topic, agent):

        prompt = f"""You are a lead researcher tasked with creating a final, consolidated report from a research log. The log details a multi-step investigation that evolved over several iterations. Your report should synthesize the findings from the *entire* process into a single, comprehensive narrative.

### Final Report Task

**Original Topic of Inquiry:**
{origin_topic}"""
        for i in range(len(self.all_research)):
            new_prompt = f"""**Iteration {i+1}:**
* **Topic Focus:** {self.all_research[i]['topic']}
* **Analysis:** {self.all_research[i]['analysis']}
* **Criticism:** {self.all_research[i]['criticism']}
* **Synthesized Conclusion for this Step:** {self.all_research[i]['synthesis']}
* **Next Question Proposed:** {self.all_research[i]['next_question']}"""
            prompt += new_prompt

        final_insturctions = """### Final Instructions
    Based on the full research log from all iterations, produce a final, detailed report on the original topic: **"{origin_topic}"**. Your report should not just summarize the final step, but should trace the key findings and shifts in understanding that occurred throughout the investigation. Synthesize all the collected information into a definitive, well-structured conclusion."""
        prompt += final_insturctions

        report = agent.model.get_response(prompt)
        return report

    def split_response_and_thinking(
        text: str, prefix: str = "<think>"
    ) -> Tuple[str, List[str]]:
        """
        Splits an LLM’s output into:
        - response: the text with all think-blocks removed
        - thinking: a list of the contents of each think-block

        A think-block is any chunk starting with `prefix` and running
        up to the next `prefix` or end-of-string.
        """
        # escape prefix for regex use
        marker = re.escape(prefix)

        # 1) extract all think blocks
        think_pattern = rf"{marker}\s*(.*?)(?=\s*{marker}|$)"
        thinking = [
            blk.strip() for blk in re.findall(think_pattern, text, flags=re.DOTALL)
        ]

        # 2) remove all think blocks from the original text
        remove_pattern = rf"{marker}\s*.*?(?=\s*{marker}|$)"
        response = re.sub(remove_pattern, "", text, flags=re.DOTALL).strip()

        return response, thinking
