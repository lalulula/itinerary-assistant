import os
from dotenv import load_dotenv
import yaml
import chainlit as cl
from openai import AzureOpenAI
from tavily import TavilyClient
from questions import *


load_dotenv()

client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version=os.environ["OPENAI_API_VERSION"],
)

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

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
activity_prompt= prompts['activity_prompt']
itinerary_prompt= prompts['itinerary_prompt']


@cl.on_message
async def on_message(msg: cl.Message):
    user_input = msg.content.strip()
    index = cl.user_session.get("question_index")
    trip_data = cl.user_session.get("trip_data") or {}

    if index == len(QUESTIONS):
        if user_input.lower() in ["no", "nope", "nothing", "that's all", "nah"]:
            await generate_itinerary(trip_data)
            # bullet_list = "\n".join([f"- **{k.capitalize()}**: {v}" for k, v in trip_data.items()])
            # await cl.Message(content=f"Great! Here's the information you've shared:\n\n{bullet_list}").send()
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



async def generate_itinerary(trip_data):
    # Format activity prompt
    activity_prompt = prompts["activity_prompt"]
    activity_filled = activity_prompt \
        .replace("{{companion}}", trip_data["companion"]) \
        .replace("{{location}}", trip_data["location"]) \
        .replace("{{interest}}", trip_data["interest"]) \
        .replace("{{activity_type}}", "active" if trip_data["active"] else "relaxed")

    activity_response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[{"role": "system", "content": activity_filled}]
    )
    activities = activity_response.choices[0].message.content

    # Get food spots via Tavily
    food_results = tavily.search(query=f"Good food places in {trip_data['location']}", max_results=5)
    food_text = "\n".join([f"- [{r['title']}]({r['url']})" for r in food_results['results']])

    # Format final itinerary prompt
    final_prompt = prompts["itinerary_prompt"] \
        .replace("{{location}}", trip_data["location"]) \
        .replace("{{duration}}", trip_data["duration"]) \
        .replace("{{companion}}", trip_data["companion"]) \
        .replace("{{budget}}", trip_data["budget"] or "not specified") \
        .replace("{{interest}}", trip_data["interest"]) \
        .replace("{{activity_type}}", "active" if trip_data["active"] else "relaxed") \
        .replace("{{activities}}", activities) \
        .replace("{{food_text}}", food_text)

    itinerary_response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[{"role": "system", "content": final_prompt}]
    )

    itinerary = itinerary_response.choices[0].message.content.strip()
    await cl.Message(content="Here's your personalized itinerary:\n\n" + itinerary).send()