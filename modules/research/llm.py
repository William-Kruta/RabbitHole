import json
import logging
import ollama
import datetime as dt
import requests


class LLM:
    """Enhanced version of OllamaModel with research-specific features"""

    def __init__(self, model_name: str, system_prompt: str, history: list = None):
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.history = history or []
        self.conversation_id = dt.datetime.now().isoformat()

        if not self.history:
            self.history.append({"role": "system", "content": self.system_prompt})

    def get_response(
        self,
        prompt: str,
        temperature: float = 0.5,
        top_p: float = 0.9,
        context_window: int = 4096,
        max_tokens: int = 2048,
    ) -> str:
        """Enhanced response method with better error handling and logging"""
        try:
            self.history.append({"role": "user", "content": prompt})

            model_options = {
                "temperature": temperature,
                "top_p": top_p,
                "num_ctx": context_window,
                "num_predict": max_tokens,
            }

            response = ollama.chat(
                model=self.model_name, messages=self.history, options=model_options
            )
            assistant_reply = response["message"]["content"]
            self.history.append({"role": "assistant", "content": assistant_reply})

            return assistant_reply

        except Exception as e:
            logging.error(f"Error getting response from {self.model_name}: {e}")
            return f"Error: {str(e)}"

    def get_response_with_tools(
        self,
        prompt: str,
        tools: list = None,
        temperature: float = 0.5,
        top_p: float = 0.9,
        context_window: int = 4096,
        max_tokens: int = 2048,
    ):
        """
        Gets a response from the model, with support for tools.
        Returns the entire message object from the assistant.
        """
        try:
            # Add user prompt to history if provided
            if prompt:
                self.history.append({"role": "user", "content": prompt})

            model_options = {
                "temperature": temperature,
                "top_p": top_p,
                "num_ctx": context_window,
                "num_predict": max_tokens,
            }

            # The ollama library expects the 'tools' parameter at the top level
            response = ollama.chat(
                model=self.model_name,
                messages=self.history,
                tools=tools,
                options=model_options,
            )

            assistant_reply_message = response["message"]
            self.history.append(assistant_reply_message)

            return assistant_reply_message

        except Exception as e:
            logging.error(f"Error getting response from {self.model_name}: {e}")
            return {"role": "assistant", "content": f"Error: {str(e)}"}

    def add_tool_response(self, tool_call_id: str, content: str):
        """Adds the result of a tool call to the history."""
        self.history.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,  # This field is important for some models, though not strictly required by Ollama yet
                "content": content,
            }
        )

    def clear_history(self, keep_system: bool = True):
        """Clear conversation history"""
        if keep_system and self.history and self.history[0]["role"] == "system":
            self.history = [self.history[0]]
        else:
            self.history = []

    def save_conversation(self, filepath: str):
        """Save conversation history to file"""
        conversation_data = {
            "model": self.model_name,
            "conversation_id": self.conversation_id,
            "timestamp": dt.datetime.now().isoformat(),
            "history": self.history,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)

    def load_conversation(self, filepath: str):
        """Load conversation history from file"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.history = data.get("history", [])
            self.conversation_id = data.get(
                "conversation_id", dt.datetime.now().isoformat()
            )

    def check_connection(self, url: str = "http://localhost:11434"):
        try:
            response = requests.get(url, timeout=5)  # Short timeout to avoid hanging
            return response.status_code == 200
        except requests.ConnectionError:
            return False
