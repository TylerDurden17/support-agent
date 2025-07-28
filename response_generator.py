from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from knowledge_base import KnowledgeBase
from ticket_classifier import create_classifier
import os
from dotenv import load_dotenv

load_dotenv()

class ResponseGenerator:
    # four critical objects get instantiated
    def __init__(self):

        # instantiates the Groq client
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.knowledge_base = KnowledgeBase()

        # returns a LangChain chain that's been configured to output structured classification data. (another LLM call under the hood with a specific prompt template.)
        self.classifier = create_classifier()

        # a ChatPromptTemplate with system/user message structure
        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a customer support agent. Use ONLY the provided context to answer.
            
            Rules:
            - Be empathetic and professional
            - If billing issue, be extra careful with specifics
            - If urgent, acknowledge immediately
            - If context doesn't contain the answer, say so and offer to escalate
            
            Context: {context}
            Classification: {classification}"""),
            ("user", "Customer: {question}")
        ])
        
        # LangChain's pipe operator
        # combines the prompt with the LLM and output parser, creates the actual LangChain pipeline
        # The prompt template formats inputs, pipes to the LLM, then pipes to the parser. 
        # It's functional composition - each stage transforms the data and passes it forward.
        self.chain = self.response_prompt | self.llm | StrOutputParser()
        
    def generate_response(self, ticket_text):
        # Get ticket classification
        # This is where the ticket text is classified into categories, priorities, and sentiments
        classification = self.classifier.invoke({"ticket_text": ticket_text})
        
        relevant_docs = self.knowledge_base.search(ticket_text, k=5)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Generate response
        # executes the main chain - the prompt template interpolates the variables, 
        # sends the formatted prompt to Groq's API, gets back token predictions, and 
        # the string parser extracts just the text content.
        response = self.chain.invoke({
            "context": context,
            "classification": classification,
            "question": ticket_text
        })
        
        return {
            "response": response,
            "classification": classification,
            "sources": [doc.metadata.get("source", "unknown") for doc in relevant_docs]
        }

if __name__ == "__main__":
    # calls the constructor.
    generator = ResponseGenerator()
    
    result = generator.generate_response("I can't cancel my subscription")
    print("Response:", result['response'])
    print("Classification:", result['classification'])