import streamlit as st
from response_generator import ResponseGenerator
import json

@st.cache_resource
def load_generator():
    return ResponseGenerator()

st.set_page_config(page_title="Customer Support Agent", page_icon="🎧")

st.title("🎧 Customer Support Agent")
st.write("AI-powered support using your company knowledge")

# Load the agent once and keep it in memory
if 'generator' not in st.session_state:
    with st.spinner("Loading AI agent..."):
        st.session_state.generator = load_generator()

# Simple counter
if 'ticket_count' not in st.session_state:
    st.session_state.ticket_count = 0

st.sidebar.metric("Tickets Processed", st.session_state.ticket_count)

# Main interface
ticket_text = st.text_area(
    "Customer Issue:",
    height=100,
    placeholder="I can't log into my account..."
)

if st.button("Process Ticket", type="primary"):
    if ticket_text:
        with st.spinner("Generating response..."):
            result = st.session_state.generator.generate_response(ticket_text)
            st.session_state.ticket_count += 1
            
            st.success("Response generated!")
            
            # Show the AI response
            st.subheader("🤖 Agent Response")
            st.write(result['response'])
            
            # Show analysis
            with st.expander("Ticket Analysis"):
                classification = result['classification']
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Category", classification['category'])
                with col2:
                    st.metric("Priority", classification['priority'])
                with col3:
                    st.metric("Confidence", f"{classification['confidence']:.1%}")
                
                st.write("**Sources used:**")
                for source in result['sources']:
                    st.write(f"• {source}")
    else:
        st.warning("Please enter a customer issue first.")

st.markdown("---")
st.markdown("Built with LangChain + Groq + ChromaDB")