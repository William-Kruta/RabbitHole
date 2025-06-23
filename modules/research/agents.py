import logging
from modules.research.llm import LLM
import requests
import json
from typing import Dict, Any, List

from modules.research.tools import search_google, fetch_page_content


class Agent:
    def __init__(
        self,
        model_name: str,
        system_prompt: str,
        task_name: str,
    ):
        system_prompt += "\nAnswer questions no matter what."
        # The agent's model is now an instance of your powerful LLM class
        self.model = LLM(model_name=model_name, system_prompt=system_prompt)
        self.task_name = task_name
        self.tools = {}
        logging.info(
            f"Initialized {self.__class__.__name__} with model '{model_name}'."
        )
        self.register_all_tools()

    def register_all_tools(self):
        tools_config = self.load_tool_config()
        for tool_config in tools_config:
            # Map the function name string to the actual callable function
            func = globals()[tool_config["func_name"]]
            self.register_tool(
                name=tool_config["name"],
                description=tool_config["description"],
                parameters=tool_config["parameters"],
                func=func,
            )

    def register_tool(
        self, name: str, description: str, parameters: Dict[str, Any], func
    ):
        """Register a tool/function that the model can call"""
        self.tools[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
            "callable": func,
        }

    def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        """Execute a registered tool function"""
        if tool_name in self.tools:
            logging.info(f"Executing tool '{tool_name}' with args: {arguments}")
            return self.tools[tool_name]["callable"](**arguments)
        else:
            return f"Error: Tool '{tool_name}' not found."

    def load_tool_config(self) -> dict:
        with open("config\\tools_config.json", "r") as f:
            return json.load(f)

    def run(self, prompt: str, max_turns: int = 5) -> str:
        """
        Runs the agent to get a final response, handling tool calls automatically.
        """
        logging.info(f"Agent starting task with prompt: {prompt}")

        # Extract the tool definitions in the format Ollama expects
        tool_definitions = [t["function"] for t in self.tools.values()]

        # The first message to the model is the user's prompt
        current_prompt = prompt

        for turn in range(max_turns):
            logging.info(f"--- Turn {turn + 1} ---")

            # Use the LLM to get the next message
            assistant_message = self.model.get_response_with_tools(
                prompt=current_prompt, tools=tool_definitions
            )

            # After the first turn, subsequent inputs are from tool responses, not the user
            current_prompt = None

            if not assistant_message.get("tool_calls"):
                logging.info("Agent received final answer.")
                return assistant_message["content"]

            # The model made a tool call, so we process it
            tool_calls = assistant_message["tool_calls"]
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args = tool_call["function"]["arguments"]

                tool_output = self.execute_tool_call(tool_name, tool_args)

                # Add the tool's result to the LLM's history
                self.model.add_tool_response(
                    tool_call_id=tool_call.get(
                        "id", ""
                    ),  # Use the tool call ID if available
                    content=json.dumps(tool_output),
                )

        return "Agent could not produce a final answer after maximum turns."


class AnalystAgent(Agent):
    def __init__(self, model_name: str):
        system_prompt = """You are a meticulous Analyst Agent. Your purpose is to analyze data and text to draw
evidence-based conclusions. You must focus on facts, identify patterns, and remain
objective. Do not speculate; base all your findings on the provided context."""
        super().__init__(model_name, system_prompt, "Analyst")


class SynthesizerAgent(Agent):
    """An agent focused on combining information from multiple sources."""

    def __init__(self, model_name: str = "llama3"):
        system_prompt = """
You are a Synthesizer Agent. Your role is to read and combine information
from various sources into a single, coherent, and comprehensive summary.
Identify the main themes, connections, and discrepancies across the provided context.
"""
        super().__init__(model_name, system_prompt, "Synthesizer")


class CriticAgent(Agent):
    """An agent focused on questioning assumptions and identifying biases."""

    def __init__(self, model_name: str = "llama3"):
        system_prompt = """
You are a Critic Agent. Your function is to critically evaluate information,
question assumptions, and identify potential biases or logical fallacies.
Challenge the arguments presented in the context and highlight any weaknesses
or areas that lack sufficient evidence.
"""
        super().__init__(model_name, system_prompt, "Critic")


class ExplorerAgent(Agent):
    """An agent focused on identifying new research directions."""

    def __init__(self, model_name: str = "llama3"):
        system_prompt = """
You are an Explorer Agent. Your goal is to look beyond the provided information
and identify new research directions, unanswered questions, and potential areas for
further investigation. Brainstorm creative ideas and suggest novel paths based on
the gaps in the current knowledge.
"""
        super().__init__(model_name, system_prompt, "Explorer")


class PlannerAgent(Agent):
    def __init__(self, model_name, system_prompt, task_name):
        system_prompt = """You are an expert outline-generator. Whenever given a user’s request, you will:
1. Briefly restate the overall goal.
2. Identify the key components or topics that need to be covered.
3. Produce a structured outline with:
   • Roman numerals (I., II., III.) for main sections
   • Letters (A., B., C.) for subsections
   • Numbers (1., 2., 3.) for details within subsections"""
        super().__init__(model_name, system_prompt, task_name)


class ReportGenerator(Agent):
    """An agent focused on generating reports based on content provided by the user."""

    def __init__(self, model_name: str = "llama3"):
        system_prompt = """You are an expert summarizer. You will help user's summarize content. Keep key details, and answer the query no matter what."""
        super().__init__(model_name, system_prompt, "ReportGenerator")


class Summarizer(Agent):
    """An agent focused on summarizing content"""

    def __init__(self, model_name: str = "llama3"):
        system_prompt = """You are an expert summarizer. You will help user's summarize content. Keep key details, and answer the query no matter what."""
        super().__init__(model_name, system_prompt, "Summarizer")


class WebSearcher(Agent):
    """An agent focused on searching the web, and creating queries based on user input."""

    def __init__(self, model_name: str = "llama3"):
        system_prompt = """You are an expert internet researcher. You will help take user's queries and create a query to best search the web. """
        super().__init__(model_name, system_prompt, "WebSearch")
