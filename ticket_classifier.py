# how to wrap a real use-case (classifying tickets) using LangChain’s chain-of-components pattern
# It sets up your core reasoning pipeline — prompt → model → structured output.
# This example uses the Groq LLM to classify customer support tickets into categories, priorities, and sentiments.
# It demonstrates how to create a structured output using Pydantic models and LangChain's output parsers.
# Importing the ChatGroq class to interact with the Groq API using Langchain

from langchain_groq import ChatGroq
# ChatPromptTemplate is used to define and structure the prompt sent to the LLM
from langchain_core.prompts import ChatPromptTemplate
# JsonOutputParser ensures the LLM output is structured and can be parsed as JSON
from langchain_core.output_parsers import JsonOutputParser
# Pydantic's BaseModel and Field for structured data validation and type safety
from pydantic import BaseModel, Field
# Standard Python typing module
from typing import List
# For handling environment variables
import os
from dotenv import load_dotenv

# Load environment variables from a .env file (used to keep API keys safe)
load_dotenv()

# Define a data model for the expected classification output using Pydantic
class TicketClassification(BaseModel): # 📌 Pydantic model, used for data validation and parsing using Python type hints.
    category: str = Field(description="Category: billing, technical, general, account")
    priority: str = Field(description="Priority: low, medium, high, urgent")
    sentiment: str = Field(description="Sentiment: positive, neutral, negative")
    confidence: float = Field(description="Confidence score 0-1")

# Function to set up and return the Langchain "chain" that classifies tickets
def create_classifier():
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        temperature=0.1,
        api_key=os.getenv("GROQ_API_KEY")
    )
    
    parser = JsonOutputParser(pydantic_object=TicketClassification)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a customer support ticket classifier. 
        Analyze tickets and categorize them:
        
        Categories:
        - billing: Payment, refunds, charges, invoices
        - technical: Bugs, features not working, errors
        - account: Login, password, profile issues
        - general: Questions, feedback, other

        Priority levels:
        - urgent: Service down, billing errors, security issues
        - high: Features broken, important account issues
        - medium: Minor bugs, general questions
        - low: Feature requests, general feedback

        {format_instructions}"""),
        ("user", "Ticket: {ticket_text}")
    ]).partial(format_instructions=parser.get_format_instructions())  # 👈 this line fixes it

    chain = prompt | llm | parser
    return chain

# Only run this part if the script is executed directly (not imported)
if __name__ == "__main__":

    classifier = create_classifier()
    
    test_tickets = [
        "I can't log into my account, getting error 500",
        "Why was I charged twice for my subscription?",
        "The app crashes when I try to upload files",
        "Can you add dark mode to the mobile app?",
        "I was billed after I cancelled my subscription.",
        "I forgot my password and can't reset it.",
        "The download button doesn't work anymore.",
        "Please delete my account permanently.",
        "I love the new UI, thanks!",
        "Are you planning to support regional languages?",
        "Security issue: I see someone else's data in my dashboard.",
        "When is the next billing cycle?",
        "Your last update broke everything!",
        "How do I change my profile photo?"
    ]
    
    for ticket in test_tickets:
        result = classifier.invoke({"ticket_text": ticket})
        print(f"Ticket: {ticket}")
        print(f"Classification: {result}")
        print("---")