#!/usr/bin/env python3

from pprint import pprint
import json
from pathlib import Path
import time
import requests

# Configuration

# TODO: read the file ~/.ilaas.key
api_key = "APIKEY"
try:
    with open(Path.home() / ".ilaas.key", "r") as f:
        api_key = f.read().strip()
except FileNotFoundError:
    print("API key file not found. Please create a file at ~/.ilaas.key with your API key.")
    exit(1)

base_url = "https://llm.ilaas.fr/v1"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Récupération des modèles
def get_ilaas_models():
    response = requests.get(f"{base_url}/models",
                            headers=headers)
    models = response.json()
    print("Available models:")
    pprint(models)
    model_name = models['data'][0]['id']
    return model_name

# On choisit un modèle par défaut
# TODO: comment le choisir intelligemment ?

# default_model_name = get_ilaas_models()
# default_model_name = "qwen-3-30b"  # XXX: pas disponible ?
default_model_name = "llama-3.3-70b"
default_model_name = "gemma-4-31b"
default_model_name = "gpt-oss-120b"


example_prompt = "Bonjour, peux-tu me parler en détails du Lycée Jean-Baptiste Kléber à Strasbourg, s'il-vous-plaît ? Sois concis avant tout, si possible précis tout en restant factuellement correct. Merci !"

default_system_prompt = "Tu es une IA utile, tu réponds rapidement et sans bavardage."


# Fonction de demande de complétion
def response_from_ilaas_llm(prompt=example_prompt, system_prompt=default_system_prompt, additionnal_messages=None, model_name=default_model_name):
    if not prompt:
        raise ValueError

    print(f"Model name: {model_name}")

    print("System prompt:")
    print(system_prompt)

    print("Prompt:")
    print(prompt)

    user_prompt = [
        {"type": "text", "text": prompt}
    ]
    # Une solution qui permettrait plus tard d'ajouter des images au message
    if additionnal_messages:
        for additionnal_message in additionnal_messages:
            user_prompt.append(
                {"type": "text", "text": additionnal_message}
            )

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": f"{system_prompt}"},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "max_tokens": 4096,
    }

    start_timer = time.time()

    response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload)
    result = response.json()

    end_timer = time.time()

    print("Reponse:")
    pprint(result)

    delta_timer = end_timer - start_timer
    print(f"Time for this response: {delta_timer:.2f} seconds")

    # Affichage de la réponse
    response = result['choices'][0]['message']['content']
    print(response)

    return response, result, delta_timer


if __name__ == "__main__":
    response_from_ilaas_llm()
