import streamlit as st
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from fpdf import FPDF

load_dotenv()

class PlannerState(TypedDict):
    messages: Annotated[List[AIMessage | HumanMessage], 'This message contains the conversation']
    city: str
    period: str
    interests: List[str]
    itinerary: str

llm = AzureChatOpenAI(
    model_name="gpt-4o-mini", 
    temperature=0,
)

prompt = ChatPromptTemplate.from_messages(
    [
        ('system', "You are a young, trendy, helpful travel assistant. Create a trip itinerary for {city}, that will last for {period} in a format of a markdown. Do not add any other text, such as icons, just provide the itinerary as a markdown."),
        ('human', "Create an itinerary for my trip")
    ]
)

# Define input functions
def input_city(state: PlannerState) -> PlannerState:
    city = st.text_input("Please enter the city you would like to visit", key="city_input")
    if city:
        return {
            **state,
            "city": city,
            "messages": state['messages'] + [HumanMessage(content=city)]
        }
    return state

def input_period(state: PlannerState) -> PlannerState:
    period = st.text_input("How long will your stay last?", key="period_input")
    if period:
        return {
            **state,
            "period": period,
            "messages": state['messages'] + [HumanMessage(content=period)]
        }
    return state

def input_interest(state: PlannerState) -> PlannerState:
    interests = st.text_input(f"Please enter your interests for your trip to {state['city']}, separated by commas.", key="interest_input")
    if interests:
        return {
            **state,
            "interests": [interest.strip() for interest in interests.split(',')],
            "messages": state['messages'] + [HumanMessage(content=interests)]
        }
    return state

def create_itinerary(state: PlannerState) -> PlannerState:
    st.write(f"Generating an itinerary for your trip to {state['city']}...")
    response = llm.invoke(prompt.format_messages(city=state['city'], period=state['period'], interests=','.join(state['interests'])))
    st.write(response.content)
    return {
        **state,
        "messages": state['messages'] + [AIMessage(content=response.content)],
        'itinerary': response.content
    }

workflow = StateGraph(PlannerState)
workflow.add_node("input_city", input_city)
workflow.add_node("input_period", input_period)
workflow.add_node("input_interest", input_interest)
workflow.add_node("create_itinerary", create_itinerary)

workflow.set_entry_point("input_city")
workflow.add_edge("input_city", "input_period")
workflow.add_edge("input_period", "input_interest")
workflow.add_edge("input_interest", "create_itinerary")
workflow.add_edge("create_itinerary", END)

app = workflow.compile()

def travel_planner():
    state = {
        "messages": [HumanMessage(content="")],
        "city": "",
        "period": "",
        'interests': [],
        "itinerary": ""
    }

    for output in app.stream(state):
        pass 

def main():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "city" not in st.session_state:
        st.session_state["city"] = ""
    if "period" not in st.session_state:
        st.session_state["period"] = ""
    if "interests" not in st.session_state:
        st.session_state["interests"] = []
    if "itinerary" not in st.session_state:
        st.session_state["itinerary"] = ""

    st.title("Travel Itinerary Planner")
    st.write("Welcome to the Travel Planner App! Let's create an itinerary for your trip.")
    
    if st.session_state["messages"]:
        for msg in st.session_state["messages"]:
            if isinstance(msg, HumanMessage):
                st.markdown(f"**You**: {msg.content}")
            elif isinstance(msg, AIMessage):
                st.markdown(f"**Assistant**: {msg.content}")

    city_input = input_city({
        "messages": st.session_state.get("messages", []),
        "city": st.session_state.get("city", ""),
        "period": st.session_state.get("period", ""),
        "interests": st.session_state.get("interests", []),
        "itinerary": st.session_state.get("itinerary", "")
    })
    
    period_input = input_period(city_input)
    
    interest_input = input_interest(period_input)
    
    if st.button("Generate Itinerary"):
        state_with_itinerary = create_itinerary(interest_input)
        st.session_state["messages"].append(AIMessage(content=state_with_itinerary['itinerary']))
        st.session_state["itinerary"] = state_with_itinerary['itinerary']
    
    if st.button("Regenerate Itinerary"):
        st.session_state["messages"] = []
        st.session_state["city"] = ""
        st.session_state["period"] = ""
        st.session_state["interests"] = []
        st.session_state["itinerary"] = ""

if __name__ == "__main__":
    main()
