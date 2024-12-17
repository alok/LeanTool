from flask import Flask, request, jsonify
import asyncio
from leantool import interactive_lean_check, models
import json
from datetime import datetime
from quart import Quart  # Using Quart instead of Flask for async support

app = Quart(__name__)

def create_chat_completion_response(result):
    """Convert lean tool result into OpenAI-compatible response format"""
    if not result.get("messages"):
        return {
            "error": {
                "message": "No messages in result",
                "type": "internal_error",
                "code": 500
            }
        }
    
    # Get the last assistant message
    assistant_msgs = [m for m in result["messages"] if m["role"] == "assistant"]
    if not assistant_msgs:
        return {
            "error": {
                "message": "No assistant response in result",
                "type": "internal_error",
                "code": 500
            }
        }
    
    last_assistant_msg = assistant_msgs[-1]
    
    response = {
        "id": f"chatcmpl-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": request.json.get("model", "default"),
        "choices": [
            {
                "index": 0,
                "message": last_assistant_msg,
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": -1,  # We don't track these
            "completion_tokens": -1,
            "total_tokens": -1
        }
    }
    
    return response

@app.route("/v1/chat/completions", methods=["POST"])
async def chat_completions():
    try:
        data = await request.get_json()
        
        if not data:
            return jsonify({
                "error": {
                    "message": "No JSON data provided",
                    "type": "invalid_request_error",
                    "code": 400
                }
            }), 400
        
        # Extract required fields
        messages = data.get("messages", [])
        if not messages:
            return jsonify({
                "error": {
                    "message": "No messages provided",
                    "type": "invalid_request_error",
                    "code": 400
                }
            }), 400
        
        # Get model from request or use default
        model = data.get("model", "sonnet")
        if model not in models:
            model = "sonnet"  # Default to sonnet if unknown model
            
        # Extract other parameters
        temperature = data.get("temperature", 0.1)
        max_attempts = data.get("max_attempts", 5)
        
        # Process through lean tool
        result = await interactive_lean_check(
            proof_request=messages[-1]["content"],
            model=models[model],
            temperature=temperature,
            max_attempts=max_attempts,
            messages=messages[:-1]  # Pass previous messages for context
        )
        
        # Convert result to OpenAI format
        response = create_chat_completion_response(result)
        
        if "error" in response:
            return jsonify(response), 500
            
        return jsonify(response)
        
    except Exception as e:
        import traceback
        print("Error:", str(e))
        print("Traceback:", traceback.format_exc())
        return jsonify({
            "error": {
                "message": str(e),
                "type": "internal_error",
                "code": 500,
                "traceback": traceback.format_exc()
            }
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
