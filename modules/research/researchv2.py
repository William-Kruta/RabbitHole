import time
import datetime as dt
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
        model = "gemma3:12b"
        self.analyst = AnalystAgent(model)
        self.critic = CriticAgent(model)
        self.explorer = ExplorerAgent(model)
        self.synthesizer = SynthesizerAgent(model)
        self.step_str = ""
        self.report = ""
        self.all_research = []
        self.status_callback = status_callback

    def set_step_str(self, text: str, current_step: int, max_steps: int):
        """Sets the step string and calls the callback to update the GUI."""
        self.step_str = text
        if self.status_callback:
            self.status_callback((text, current_step, max_steps))

    def start_research(
        self, topic: str, research_iterations: int = 3, web_iterations: int = 5
    ):
        origin_topic = topic
        current_topic = topic
        index = 0
        current_step = 0
        num_operations = 5  # web, analyze, critisize, synthesize, explore
        max_steps = research_iterations * num_operations
        for i in range(research_iterations):
            start = time.time()
            current_step += 1
            index_str = index + 1
            self.set_step_str(
                f"====================\n[{index_str}.0] Topic: {current_topic}",
                current_step,
                max_steps,
            )
            self.set_step_str(
                f"[{index_str}.1] Searching the web...",
                current_step,
                max_steps,
            )
            refined_web_prompt = self.refine_query_for_web(topic)
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
            analysis = analyze(current_topic, content, self.analyst, 4096)
            # Critisize
            current_step += 1
            self.set_step_str(
                f"[{index_str}.3] Critisizing analysis...", current_step, max_steps
            )
            criticism = critisize(analysis, content, self.critic, 4096)
            # Synthesize
            current_step += 1
            self.set_step_str(
                f"[{index_str}.4] Synthesizing responses...", current_step, max_steps
            )
            synthesis = synthesize(analysis, criticism, self.synthesizer, 4096)
            # Explore
            current_step += 1
            self.set_step_str(
                f"[{index_str}.5] Generating next question...", current_step, max_steps
            )
            next_question = next_step(synthesis, origin_topic, self.explorer, 4096)
            current_topic = next_question
            index += 1

            end = time.time()
            elapse = end - start
            self.all_research.append(
                {
                    "topic": current_topic,
                    "web_query": refined_web_prompt,
                    "sources": urls,
                    "analysis": analysis,
                    "criticism": criticism,
                    "synthesis": synthesis,
                    "next_question": next_question,
                    "elapse": elapse,
                }
            )

        self.report = self.generate_report(origin_topic, self.analyst)
        self.set_step_str(
            f"\nResearch complete for topic: '{origin_topic}'!", max_steps, max_steps
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
