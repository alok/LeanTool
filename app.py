import streamlit as st
import asyncio
from typing import Dict, Any
import json

# Import your existing lean tool functions
from leantool import interactive_lean_check  # Assuming your code is in lean_tool.py

async def process_message(message: str, history=None) -> Dict[str, Any]:
    """Process a message through the Lean tool"""
    result = await interactive_lean_check(
        proof_request=message,
        #model="gpt-4o",
        #temperature=0.1,
        #max_attempts=5
        messages=history
    )
    return result

def format_attempt(attempt: Dict[str, Any]) -> str:
    """Format an attempt for display"""
    output = []
    if "code" in attempt:
        output.append("Code:\n```lean\n" + attempt["code"] + "\n```")
        if "result" in attempt:
            output.append("Success: " + str(attempt["result"]["success"]))
            if attempt["result"]["output"]:
                output.append("Output: " + attempt["result"]["output"])
            if attempt["result"]["error"]:
                output.append("Error: " + attempt["result"]["error"])
    if "error" in attempt:
        output.append("Error: " + attempt["error"])
    return "\n".join(output)

def main():
    st.title("Lean Proof Assistant Chat")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to prove?"):
        # Add user message to chat history
        #st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process with Lean tool
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Run async code in sync context
                result = asyncio.run(process_message(prompt,st.session_state.messages))
                
                # Format response
                response = []
                response.append("Let me help you with that proof.")
                
                # Show attempts
                for i, attempt in enumerate(result["attempts"], 1):
                    response.append(f"\nAttempt {i}:")
                    response.append(format_attempt(attempt))
                
                # Show final result
                if result["success"]:
                    response.append("\n✅ Success! Final proof:")
                    response.append("```lean\n" + result["final_code"] + "\n```")
                else:
                    response.append("\n❌ Could not complete the proof successfully.")
                    if 'final_code' in result: response.append("```lean\n" + result["final_code"] + "\n```")

                
                # Join all parts and display
                full_response = "\n".join(response)
                st.markdown(full_response)
                
                # Add assistant response to chat history
                if "messages" in result: st.session_state.messages=result["messages"]
                else:
                  st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                  )


if __name__ == "__main__":
    main()
