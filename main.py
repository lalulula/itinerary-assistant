import os
from dotenv import load_dotenv
import yaml
import chainlit as cl
from openai import AzureOpenAI
load_dotenv()
import re


client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version=os.environ["OPENAI_API_VERSION"],
)

welcome_message = """Welcome to the Chainlit Travel Planner! 🌍✈️

To help you build the perfect itinerary, I’ll ask a few quick questions about your trip. You can also tell me directly if you already have something in mind.

Just share whatever you know — things like:
- Who you’re traveling with
- Where you’d like to go
- How long you plan to stay
- What kind of experiences or activities you’re interested in

Let’s get started whenever you’re ready!
"""



@cl.on_chat_start
async def on_chat_start():
      cl.user_session.set("message_history", [])
      await cl.Message(content=welcome_message).send()
with open('prompts.yaml', 'r') as file:
      prompts = yaml.safe_load(file)
# Access prompts
extract_keywords_prompt = prompts['extract_keywords_prompt']


@cl.on_message
async def on_message(msg: cl.Message):
    history = cl.user_session.get("message_history") or []
    history.append({"role": "user", "content": msg.content})

    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {"role": "system", "content": extract_keywords_prompt},
            *history
        ],
    )

    assistant_reply = response.choices[0].message.content.strip()
    history.append({"role": "assistant", "content": assistant_reply})

    cl.user_session.set("message_history", history)
    match = re.search(r"Here are the keywords I gathered:\s*(.*)", assistant_reply, re.DOTALL)
    if match:
      raw_keywords = match.group(1).strip()

      # Support newline, bullet points, or commas
      keyword_list = re.split(r'[\n•,]+', raw_keywords)
      keyword_list = [kw.strip() for kw in keyword_list if kw.strip()]
      print(f"[✅ Keywords Extracted]: {keyword_list}")

    await cl.Message(content=assistant_reply).send()