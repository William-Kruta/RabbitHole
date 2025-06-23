import re
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import datetime as dt
import subprocess
import json

import random
import string


def search_google(query: str, num_results: int = 5):
    try:
        urls = list(search(query, num_results=num_results))
    except requests.exceptions.HTTPError:
        urls = []
    return urls


def fetch_page_content(url: str) -> str:
    headers = generate_random_header()
    # headers = {
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    #     "Accept-Language": "en-US,en;q=0.5",
    #     "Accept-Encoding": "gzip, deflate, br",
    #     "Connection": "keep-alive",
    #     "Upgrade-Insecure-Requests": "1",
    # }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
    except requests.exceptions.ReadTimeout:
        return ""
    except requests.exceptions.MissingSchema:
        return ""
    soup = BeautifulSoup(resp.text, "html.parser")
    return "\n".join(p.get_text() for p in soup.find_all("p"))


def refine_prompt_for_web(prompt: str, agent):
    instructions = f"Based on the following prompt: '{prompt}', refine the users query for a google search. Return only the refined query. If relevant here is today's date: {dt.datetime.now().date()}. Do not put the query in quotes."
    return agent.model.get_response(instructions)


def clean_text(text: str):
    text = text.replace("\n", " ").replace("\r", "")
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def clean_multiple_texts(texts: list) -> list:
    return [clean_text(text) for text in texts]


def recommend_web_sources(prompt: str, agent):
    instructions = f"""Based on this user's query: '{prompt}', provide a list of 5 web sources to search. An example response would be: '\nReddit\nWikipedia'. Return only the web sources, and nothing else. 
"""
    response = agent.model.get_response(instructions)
    response = response.split("\n")
    return response


def list_ollama_models():
    """
    Lists all Ollama models that have been downloaded.

    Returns:
        list: A list of strings, where each string is the name of a downloaded model.
              Returns an empty list if no models are found or if there's an error.
    """
    try:
        # Execute the 'ollama list' command and capture the output
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Parse the JSON output
        models_data = json.loads(result.stdout)

        # Extract the model names from the JSON data
        model_names = [model["name"] for model in models_data]
        return model_names

    except subprocess.CalledProcessError as e:
        print(f"Error executing 'ollama list': {e}")
        return []
    except json.JSONDecodeError:
        print("Error decoding JSON output from 'ollama list'")
        return []
    except FileNotFoundError:
        print(
            "Ollama command not found.  Please ensure Ollama is installed and in your system's PATH."
        )
        return []


def generate_random_header():
    """
    Generates a random HTTP header dictionary.

    Returns:
    dict: A dictionary representing a random HTTP header.
    """

    # Lists of possible values for headers. Expand these for more variety.
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3906.99 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 13_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.6.1 Mobile/17H38 Safari/605.1.15",
    ]

    accepts = [
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "application/json",
        "application/xml",
        "image/gif, image/jpeg, image/png",
    ]

    accept_languages = [
        "en-US,en;q=0.5",
        "es-ES,es;q=0.8",
        "fr-FR,fr;q=0.7",
        "de-DE,de;q=0.6",
    ]

    accept_encodings = [
        "gzip, deflate, br",
        "gzip",
        "deflate",
        "*",
    ]

    connections = ["keep-alive", "close"]

    upgrade_insecure_requests = [
        "1",
        "0",
    ]

    # Randomly select values for each header
    random_header = {
        "User-Agent": random.choice(user_agents),
        "Accept": random.choice(accepts),
        "Accept-Language": random.choice(accept_languages),
        "Accept-Encoding": random.choice(accept_encodings),
        "Connection": random.choice(connections),
        "Upgrade-Insecure-Requests": random.choice(upgrade_insecure_requests),
    }

    return random_header
