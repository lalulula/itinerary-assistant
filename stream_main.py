import os
from dotenv import load_dotenv
import yaml
import chainlit as cl
from openai import AzureOpenAI,AsyncAzureOpenAI
load_dotenv()

client = AsyncAzureOpenAI(api_key=os.environ["AZURE_OPENAI_API_KEY"])

@cl.on_chat_start
def on_chat_start():
      print("New chat started. How can I help you today?")
      cl.user_session.set("message_history", [{"role":"system","content":"You are a helpful assistant specialized in travel planning. You will be given a user's request and you will need to extract the keywords from the request."}])
with open('prompts.yaml', 'r') as file:
      prompts = yaml.safe_load(file)
# Access prompts
extract_keywords_prompt = prompts['extract_keywords_prompt']



@cl.step(type='tool')
async def dummy_tool():
      await cl.sleep(2)
      return 'Then will return a response after 2 seconds'


@cl.on_message
async def on_message(msg: cl.Message):
    message_history = cl.user_session.get("message_history")
    full_prompt = f'{extract_keywords_prompt}\nInput: "{msg.content}"\nOutput:'
    message_history.append({"role": "user", "content": full_prompt})
    
    cl_msg = cl.Message(content="")

    stream = await client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=message_history,
        stream=True
    )

    async for part in stream:
        token = "" 
        if part.choices and hasattr(part.choices[0], "delta") and part.choices[0].delta:
            token = getattr(part.choices[0].delta, "content", "")
        if token:
            await cl_msg.stream_token(token)

    message_history.append({"role": "assistant", "content": cl_msg.content})
    print(message_history)
    await cl_msg.update()
