import asyncio
from leantool import interactive_lean_check

async def chat_loop():
    print("Welcome to Lean Proof Assistant Chat!")
    print("Type 'exit' to quit\n")
    print("Type 'reset' to reset message history\n")
    
    messages=None
    while True:
        # Get user input
        user_input = input("\nWhat would you like to prove? > ")
        if user_input.lower() in ['exit', 'quit']:
            break
        if user_input.lower() == 'reset':
            messages=None
            continue
        print("\nProcessing...")
        try:
            result = await interactive_lean_check(
                proof_request=user_input,
                #model="gpt-4",
                #temperature=0.1,
                #max_attempts=5
                messages=messages
            )

            # Display results
            print("\nAttempts:")
            for i, attempt in enumerate(result["attempts"], 1):
                print(f"\nAttempt {i}:")
                if "code" in attempt:
                    print("Code:")
                    print(attempt["code"])
                    if "result" in attempt:
                        print("Success:", attempt["result"]["success"])
                        if attempt["result"]["error"]:
                            print("Error:", attempt["result"]["error"])
                elif "error" in attempt:
                    print("Error:", attempt["error"])
            
            if result["success"]:
                print("\n✅ Success! Final proof:")
                print(result["final_code"])
            else:
                print("\n❌ Could no complete the proof successfully.")
                if 'final_code' in result: print(result["final_code"])
            if 'messages' in result:
                messages=result["messages"]
            else:
                print("\nResult did not return message history. Leaving messages as is:")
                print('\n\n'.join(messages))


        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(chat_loop())
