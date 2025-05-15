import os
from dotenv import load_dotenv
import yaml
import chainlit as cl
from openai import AzureOpenAI
import re


load_dotenv()

QUESTIONS = [
    {"key": "location", "text": "1. Which location are you planning to travel to?"},
    {"key": "duration", "text": "2. How long is your trip? (e.g., 5 days, 1 week)"},
    {"key": "companion", "text": "3. Who will be coming with you? (e.g., solo, partner, friends, family)"},
    {"key": "active", "text": "4. Do you want an active trip or a relaxed one? (Type: active / relaxed)"},
    {"key": "budget", "text": "5. What's your budget level? (e.g., luxury, mid-range, budget) — or you can skip this."},
    {"key": "interest", "text": "6. Do you have any specific interests or themes? (e.g., food, culture, beach, hiking)"},
]

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("message_history", [])
    cl.user_session.set("question_index", 0)
    cl.user_session.set("trip_data", {})
    await cl.Message(content=QUESTIONS[0]["text"]).send()


with open('prompts.yaml', 'r') as file:
      prompts = yaml.safe_load(file)
# Access prompts
extract_keywords_prompt = prompts['extract_keywords_prompt']


@cl.on_message
async def on_message(msg: cl.Message):
    user_input = msg.content.strip()
    index = cl.user_session.get("question_index")
    trip_data = cl.user_session.get("trip_data") or {}

    if index == len(QUESTIONS):
        if user_input.lower() in ["no", "nope", "nothing", "that's all", "nah"]:
            bullet_list = "\n".join([f"- **{k.capitalize()}**: {v}" for k, v in trip_data.items()])
            await cl.Message(content=f"Great! Here's the information you've shared:\n\n{bullet_list}").send()
            return
        else:
            # Save extra info
            trip_data["etc"] = user_input
            cl.user_session.set("trip_data", trip_data)
            await cl.Message(content="Thanks! Anything else you'd like to add? (If not, just say 'no')").send()
            return

    # Map user input to field
    question_key = QUESTIONS[index]["key"]

    # Convert to boolean if it's the active/relaxed question
    if question_key == "active":
        if user_input.lower() in ["active", "yes"]:
            trip_data["active"] = True
        elif user_input.lower() in ["relaxed", "no"]:
            trip_data["active"] = False
        else:
            await cl.Message(content="Please type 'active' or 'relaxed'.").send()
            return
    else:
        trip_data[question_key] = user_input if user_input.lower() != "skip" else None

    cl.user_session.set("trip_data", trip_data)
    cl.user_session.set("question_index", index + 1)

    # Ask next question or move to final confirmation
    if index + 1 < len(QUESTIONS):
        await cl.Message(content=QUESTIONS[index + 1]["text"]).send()
    else:
        await cl.Message(content="Would you like to add anything else before I generate your itinerary?").send()
