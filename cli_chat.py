import asyncio
import jsonlines
from leantool import interactive_lean_check

async def chat_loop():
    print("Welcome to Lean Proof Assistant Chat!")
    print("Type 'multi ENDINPUT' to start a multiline input starting from the next line, ending with a line of only 'ENDINPUT'")
    print("Type 'exit' to quit")
    print("Type 'reset' to reset message history")
    print("Type 'save filename' to save message history")
    print("Type 'load filename' to load a text file to be read by the LLM")
    print("Type 'resume filename' to resume from chat history\n")

    messages=None
    files=[]
    while True:
        # Get user input
        user_input = input("\nWhat would you like to prove? > ")
        if user_input.lower() in ['exit', 'quit']:
            break
        if user_input.lower() == 'reset':
            messages=None
            continue
        if user_input.lower().startswith('save'):
            fn = user_input.split()[1]
            with jsonlines.open(fn, mode='w') as writer:
                writer.write_all(messages)
            continue
        if user_input.lower().startswith('load'):
            fn=user_input.split()[1]
            files.append(fn)
            continue
        if user_input.lower().startswith('resume'):
            fn=user_input.split()[1]
            with jsonlines.open(fn) as reader:
                messages=[m for m in reader]
            continue
        if user_input.lower().startswith('multi'):
            endstr=user_input.split()[1]
            user_input=''
            while True:
                line=input()
                if line==endstr: break
                user_input+=line

        print("\nProcessing...")
        try:
            result = await interactive_lean_check(
                proof_request=user_input,
                #model="gpt-4",
                #temperature=0.1,
                #max_attempts=5
                files=files,
                messages=messages
            )
            files=[]

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
            
            if 'messages' in result:
                messages=result["messages"]
                print(messages[-1]['content'])
            else:
                print("\nResult did not return message history. Leaving messages as is:")
                print('\n\n'.join(messages))
            if result["success"]:
                print("\n✅ Success! Final proof:")
                print(result["final_code"])
            else:
                print("\n❌ Could no complete the proof successfully.")
                if 'final_code' in result: print(result["final_code"])


        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(chat_loop())
