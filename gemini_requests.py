#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# Script de test d'appel à l'API Gemini de Google

from pprint import pprint
import json
import streamlit as st
from pathlib import Path
import time
# import requests

try:
    from google import genai
    from google.genai import types
except ImportError as exception:
    print("The 'google.genai' package is not installed. Please install it using 'pip install google-genai'.")
    raise exception

# Configuration

# Read the file ~/.gemini_api.key
api_key = None
try:
    with open(Path.home() / ".gemini_api.key", "r") as f:
        print("Reading the GOOGLE_API_KEY from ~/.gemini_api.key ...")
        api_key = f.read().strip()
except FileNotFoundError:
    print("API key file not found. Please create a file at ~/.gemini_api.key with your API key.")

if not api_key:
    print("Reading the 'GOOGLE_API_KEY' secret from streamlit's secrets (.streamlit/secrets.toml)...")
    api_key = st.secrets["GOOGLE_API_KEY"]


help_credits_llm = "Avec une requête *payante* à l'IA Google Gemini, via Google AI Studio. Cf. https://aistudio.google.com/ si vous souhaitez configurer votre propre accès ou monitorer le coût de vos requêtes précédentes"

gemini_client = genai.Client(api_key=api_key)

default_model = 'gemini-flash-latest'

# prompt_initial = """Analyse ce sujet de TP d'informatique. Identifie les exercices et questions. Propose un barème sur 20 points en respectant la difficulté relative des notions (ex: récursivité en OCaml vs manipulation de pointeurs en C). Retourne uniquement un JSON sous la forme : {"questions": [{"id": "1.a", "description": "...", "points": 2}]}"""


example_prompt = "Bonjour, peux-tu me parler en détails du Lycée Jean-Baptiste Kléber à Strasbourg, s'il-vous-plaît ? Sois concis avant tout, si possible précis tout en restant factuellement correct. Merci !"

default_system_prompt = ""


def response_from_llm(
        prompt=example_prompt,
        system_prompt=default_system_prompt,
        additionnal_messages=None,
        paths_pdf=None,
        paths_json=None,
        paths_source=None,
        model_name=default_model,
        force_json_response=False,
    ):
    print(f"Model name: {model_name}")

    contents = []

    if system_prompt:
        print("System prompt:")
        print(system_prompt)
        contents.append(system_prompt)

    if paths_pdf:
        for chemin_pdf in paths_pdf:
            with open(chemin_pdf, "rb") as f:
                pdf_data = f.read()
                contents.append(
                    types.Part.from_bytes(data=pdf_data, mime_type="application/pdf")
                )

    if paths_json:
        for chemin_json in paths_json:
            with open(chemin_json, "rb") as f:
                json_data = f.read()
                contents.append(
                    types.Part.from_bytes(data=json_data, mime_type="application/json")
                )

    if paths_source:
        for chemin_source in paths_source:
            with open(chemin_source, "r", encoding="utf-8") as f:
                source_data = f.read()
                contents.append(
                    types.Part.from_text(text=source_data)
                )

    if additionnal_messages:
        contents.extend(additionnal_messages)

    contents.append(prompt)

    start_timer = time.time()

    response_mime_type = "text/plain"
    if force_json_response:
        response_mime_type = "application/json"  # Force le format JSON

    response = gemini_client.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type=response_mime_type,
        )
    )

    end_timer = time.time()

    print("Response:")
    pprint(response)

    delta_timer = end_timer - start_timer
    print(f"Time for this response: {delta_timer:.2f} seconds")

    return response.text


if __name__ == "__main__":
    example_prompt = "Bonjour, peux-tu me parler en détails du Lycée Jean-Baptiste Kléber à Strasbourg, s'il-vous-plaît ? Sois concis avant tout, si possible précis tout en restant factuellement correct. Merci !"

    default_system_prompt = "Tu es une IA utile, tu réponds rapidement et sans bavardage."

    response_from_llm(
        prompt=example_prompt,
        system_prompt=default_system_prompt,
        # additionnal_messages=None,
        # paths_pdf=None,
        # paths_json=None,
        # model_name=default_model,
        # force_json_response=False,
    )
