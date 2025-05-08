import os
from dotenv import load_dotenv
import yaml
import chainlit as cl
from openai import AzureOpenAI
load_dotenv()

client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_version=os.environ["OPENAI_API_VERSION"],
)


@cl.on_chat_start
def on_chat_start():
      print("New chat started. How can I help you today?")
      cl.user_session.set("message_history", [{"role":"system","content":"You are a helpful assistant specialized in travel planning. You will be given a user's request and you will need to extract the keywords from the request."}])
with open('prompts.yaml', 'r') as file:
      prompts = yaml.safe_load(file)
# Access prompts
extract_keywords_prompt = prompts['extract_keywords_prompt']

@cl.set_starters
async def set_starters():
      return [
            cl.Starter(
                  label='Exotic places',
                  message='I want to visit exotic places',
                  icon='/public/exotic.svg'
            ),
            cl.Starter(
                  label='Places to travel alone',
                  message='Create an itinerary for a solo trip',
                  icon='/public/alone.svg'
            ),
            cl.Starter(
                  label='Family trip',
                  message='Create an itinerary for a family trip.',
                  icon='/public/family.svg'
            ),
            cl.Starter(
                  label='Walking trip',
                  message='Create an itinerary for a walking trip. By walking trip I mean a trip where the only transport is your feet.',
                  icon='/public/by_foot.svg'
            )
      ]


@cl.step(type='tool')
async def dummy_tool():
      await cl.sleep(2)
      return 'Then will return a response after 2 seconds'

@cl.on_message
async def on_message(msg: cl.Message):
    full_prompt = f'{extract_keywords_prompt}\nInput: "{msg.content}"\nOutput:'

    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[{"role": "user", "content": full_prompt}],
    )

    reply = response.choices[0].message.content

    await cl.Message(content=reply).send()


