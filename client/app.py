import streamlit as st
import requests
import os
import json
from datetime import datetime

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 30

# Page config
st.set_page_config(
    page_title="Customer Support Agent", 
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .response-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #ffe6e6;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #ff4444;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #e6ffe6;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #44ff44;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'ticket_count' not in st.session_state:
    st.session_state.ticket_count = 0
if 'tickets_history' not in st.session_state:
    st.session_state.tickets_history = []
if 'api_connected' not in st.session_state:
    st.session_state.api_connected = False

def check_api_connection():
    """Check if the API server is reachable"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            st.session_state.api_connected = True
            return True, data.get("message", "API is healthy")
        else:
            st.session_state.api_connected = False
            return False, f"API returned status code: {response.status_code}"
    except requests.exceptions.ConnectionError:
        st.session_state.api_connected = False
        return False, f"Cannot connect to API server at {API_URL}"
    except requests.exceptions.Timeout:
        st.session_state.api_connected = False
        return False, "API server timeout - server may be starting up"
    except Exception as e:
        st.session_state.api_connected = False
        return False, f"Unexpected error: {str(e)}"

def call_generate_api(ticket_text):
    """Call the API to generate a response"""
    try:
        response = requests.post(
            f"{API_URL}/generate",
            json={"text": ticket_text},
            timeout=REQUEST_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", error_detail)
            except:
                error_detail = response.text or f"HTTP {response.status_code}"
            return False, f"API Error ({response.status_code}): {error_detail}"
            
    except requests.exceptions.Timeout:
        return False, f"Request timeout after {REQUEST_TIMEOUT} seconds. The AI model may be processing a complex request."
    except requests.exceptions.ConnectionError:
        return False, "Lost connection to API server. Please check if the server is running."
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def format_confidence(confidence):
    """Format confidence score as percentage"""
    try:
        return f"{float(confidence):.1%}"
    except:
        return "N/A"

def get_priority_color(priority):
    """Get color for priority badge"""
    colors = {
        "urgent": "🔴",
        "high": "🟠", 
        "medium": "🟡",
        "low": "🟢"
    }
    return colors.get(priority.lower(), "⚪")

# Main header
st.markdown('<h1 class="main-header">🎧 Customer Support Agent</h1>', unsafe_allow_html=True)
st.markdown("*AI-powered support using your company knowledge base*")

# Sidebar
with st.sidebar:
    st.header("📊 Dashboard")
    
    # API Connection Status
    st.subheader("🔗 Connection Status")
    is_connected, message = check_api_connection()
    
    if is_connected:
        st.success("✅ API Connected")
        st.caption(message)
    else:
        st.error("❌ API Disconnected")
        st.caption(message)
        if "localhost" in API_URL:
            st.info("💡 Make sure to run the server with: `cd server && python api.py`")
    
    st.divider()
    
    # Metrics
    st.subheader("📈 Metrics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tickets Processed", st.session_state.ticket_count)
    with col2:
        avg_confidence = 0
        if st.session_state.tickets_history:
            confidences = [t.get('confidence', 0) for t in st.session_state.tickets_history]
            avg_confidence = sum(confidences) / len(confidences)
        st.metric("Avg Confidence", f"{avg_confidence:.1%}")
    
    # Quick stats
    if st.session_state.tickets_history:
        st.subheader("📋 Recent Categories")
        categories = [t.get('category', 'unknown') for t in st.session_state.tickets_history[-5:]]
        for cat in set(categories):
            count = categories.count(cat)
            st.caption(f"• {cat.title()}: {count}")
    
    st.divider()
    
    # Settings
    st.subheader("⚙️ Settings")
    show_debug = st.checkbox("Show Debug Info", value=False)
    auto_classify = st.checkbox("Auto-classify tickets", value=True)
    
    if st.button("🗑️ Clear History"):
        st.session_state.tickets_history = []
        st.session_state.ticket_count = 0
        st.rerun()

# Main content area
if not is_connected:
    st.error("Cannot connect to the AI backend. Please check the server status in the sidebar.")
    st.stop()

# Input section
st.header("📝 Submit Support Ticket")

col1, col2 = st.columns([3, 1])

with col1:
    ticket_text = st.text_area(
        "Customer Issue:",
        height=120,
        placeholder="Example: I can't log into my account and keep getting an error message...",
        help="Describe the customer's issue in detail. The AI will analyze and generate an appropriate response."
    )

with col2:
    st.markdown("**Quick Examples:**")
    examples = [
        "I can't log into my account",
        "Cancel my subscription",
        "Billing question about charges",
        "App crashes on startup",
        "Password reset not working"
    ]
    
    for example in examples:
        if st.button(f"📋 {example}", key=f"example_{example}", use_container_width=True):
            st.session_state.example_text = example
            st.rerun()

# Use example text if selected
if 'example_text' in st.session_state:
    ticket_text = st.session_state.example_text
    del st.session_state.example_text

# Process button
process_col1, process_col2, process_col3 = st.columns([1, 2, 1])

with process_col2:
    process_button = st.button(
        "🚀 Process Ticket", 
        type="primary", 
        use_container_width=True,
        disabled=not ticket_text.strip()
    )

# Processing logic
if process_button and ticket_text.strip():
    with st.spinner("🤖 AI is analyzing the ticket and generating a response..."):
        progress_bar = st.progress(0)
        
        # Simulate progress for better UX
        import time
        for i in range(3):
            time.sleep(0.3)
            progress_bar.progress((i + 1) * 33)
        
        success, result = call_generate_api(ticket_text.strip())
        progress_bar.progress(100)
        
        if success:
            st.session_state.ticket_count += 1
            
            # Store in history
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'ticket': ticket_text.strip(),
                'category': result.get('classification', {}).get('category', 'unknown'),
                'priority': result.get('classification', {}).get('priority', 'medium'),
                'confidence': result.get('classification', {}).get('confidence', 0),
                'response_length': len(result.get('response', ''))
            }
            st.session_state.tickets_history.append(history_entry)
            
            # Success message
            st.markdown('<div class="success-box">✅ Response generated successfully!</div>', unsafe_allow_html=True)
            
            # Main response
            st.header("🤖 AI Agent Response")
            st.markdown(f'<div class="response-box">{result["response"]}</div>', unsafe_allow_html=True)
            
            # Analysis section
            st.header("📊 Ticket Analysis")
            
            classification = result.get('classification', {})
            
            # Metrics row
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                category = classification.get('category', 'Unknown')
                st.metric("Category", category.title())
            
            with metric_col2:
                priority = classification.get('priority', 'medium')
                priority_emoji = get_priority_color(priority)
                st.metric("Priority", f"{priority_emoji} {priority.title()}")
            
            with metric_col3:
                confidence = classification.get('confidence', 0)
                st.metric("Confidence", format_confidence(confidence))
            
            with metric_col4:
                sentiment = classification.get('sentiment', 'neutral')
                sentiment_emoji = {"positive": "😊", "neutral": "😐", "negative": "😟"}.get(sentiment, "😐")
                st.metric("Sentiment", f"{sentiment_emoji} {sentiment.title()}")
            
            # Sources section
            sources = result.get('sources', [])
            if sources:
                st.subheader("📚 Knowledge Sources Used")
                
                for i, source in enumerate(sources, 1):
                    source_name = source.replace('./support_docs/', '').replace('.txt', '')
                    st.markdown(f"**{i}.** {source_name}")
            
            # Debug information
            if show_debug:
                st.subheader("🔍 Debug Information")
                with st.expander("Raw API Response"):
                    st.json(result)
                
                with st.expander("Request Details"):
                    st.write(f"**API URL:** {API_URL}")
                    st.write(f"**Request Timeout:** {REQUEST_TIMEOUT}s")
                    st.write(f"**Ticket Length:** {len(ticket_text)} characters")
                    st.write(f"**Response Time:** Processed at {datetime.now().strftime('%H:%M:%S')}")
        else:
            # Error handling
            st.markdown(f'<div class="error-box">❌ {result}</div>', unsafe_allow_html=True)
            
            if "timeout" in result.lower():
                st.info("💡 **Tip:** The AI model might be processing a complex request. Try a shorter, more specific question.")
            elif "connection" in result.lower():
                st.info("💡 **Tip:** Check the sidebar for connection status. The server may need to be restarted.")

elif process_button and not ticket_text.strip():
    st.warning("⚠️ Please enter a customer issue before processing.")

# Footer
st.markdown("---")

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption("🔧 Built with LangChain + Groq + ChromaDB")

with footer_col2:
    if st.session_state.api_connected:
        st.caption("🟢 Backend Status: Online")
    else:
        st.caption("🔴 Backend Status: Offline")

with footer_col3:
    st.caption(f"🌐 API: {API_URL}")

# Recent tickets section (if any)
if st.session_state.tickets_history:
    st.header("📋 Recent Tickets")
    
    # Show last 3 tickets
    recent_tickets = st.session_state.tickets_history[-3:]
    
    for i, ticket in enumerate(reversed(recent_tickets), 1):
        with st.expander(f"Ticket #{len(st.session_state.tickets_history) - i + 1} - {ticket['category'].title()} ({ticket['priority'].title()})"):
            st.write(f"**Issue:** {ticket['ticket'][:100]}{'...' if len(ticket['ticket']) > 100 else ''}")
            st.write(f"**Category:** {ticket['category'].title()}")
            st.write(f"**Priority:** {get_priority_color(ticket['priority'])} {ticket['priority'].title()}")
            st.write(f"**Confidence:** {format_confidence(ticket['confidence'])}")
            st.write(f"**Processed:** {datetime.fromisoformat(ticket['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")