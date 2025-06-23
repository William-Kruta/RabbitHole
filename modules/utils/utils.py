import json
import subprocess


def get_ollama_models():
    """
    Return a list of locally downloaded Ollama models by calling the Ollama CLI.
    """
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().splitlines()
        models = []
        for line in lines:
            # skip header or empty lines
            if not line or line.upper().startswith("MODEL"):
                continue
            # first column is the model name
            parts = line.split()
            if parts:
                models.append(parts[0])
        return models
    except subprocess.CalledProcessError as e:
        print(f"Error listing Ollama models: {e}")
        return []
