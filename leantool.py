import sys
import asyncio
import subprocess
import json
from typing import Dict, Any, Optional
from litellm import completion, acompletion
import tempfile
import os
import re
import traceback

import litellm
litellm.set_verbose=True
litellm.drop_params=True

models={
  'sonnet37':'anthropic/claude-3-7-sonnet-20250219',
  'sonnet':'anthropic/claude-3-5-sonnet-20241022',
  'qwen':'ollama/hf.co/bartowski/Qwen2.5-Coder-14B-Instruct-GGUF:IQ4_XS',
  'qwen-max':'openrouter/qwen/qwen-max',
  'grok':'openrouter/x-ai/grok-2-1212',
  'deepseek': 'deepseek/deepseek-chat',
  'r1': 'deepseek/deepseek-reasoner',
  'deepseek-coder':'ollama/hf.co/bartowski/DeepSeek-Coder-V2-Lite-Instruct-GGUF:Q5_K_M',
  'deepseek-prover':'ollama/hf.co/deepseek-ai/DeepSeek-Prover-V1.5-RL',
  'o1-mini':'o1-mini',
  'o1':'o1',
  'o3-mini':'o3-mini',
  'o3-mini-high':'o3-mini-high',
  'gpt':'gpt-4o',
  'gemini':'gemini/gemini-2.0-flash-exp',
  'gemini-thinking':'gemini/gemini-2.0-flash-thinking-exp'
}


class LeanToolException(Exception):
    """Custom exception for Lean tool errors"""
    pass

SYSTEM_MESSAGE_TOOLS = """You are an assistant that writes Lean 4 code. 
You have access to a tool that can pass your code to be compiled and executed by the Lean proof assistant.

You can use the tool to:
- Verify that your Lean 4 code is syntactically valid
- Run your code with test inputs and check the results 
- Utilize Lean's interative features to return suggestions and/or information that helps you complete the task

If you believe you can directly solve the task given by the request:
1. Write initial code based on the request
2. Invoke the tool to verify it
3. If there are errors, analyze them and make modifications
4. Continue this loop until either:
   - The code is valid
   - You determine you cannot fix the issues
"""

SYSTEM_MESSAGE_PLAIN_TEXT = """You may invoke the tool by enclosing your Lean 4 code in <Try> ... </Try> tags.
Your code inside the <Try> tags will be executed by Lean and outputs including error messages will be shown to you in the next user message.
"""

SYSTEM_MESSAGE_LOAD_SORRY = """
If you believe the task is more complex and would benefit from a step by step approach:
1. Start with a proof sketch containing `sorry` placeholders.
2. Call check_lean_code. If your code is syntactically correct, the tool will output goal states corresponding to each `sorry`
3. Replace a `sorry` with a proof or a more refined proof sketch. Call check_lean_code to verify.
4. Repeat until the code is complete with no `sorry` left
"""

SYSTEM_MESSAGE_FEATURES = """
You may import libraries as needed. If you are unsure about which particular Mathlib import contains what you need, you may `import Mathlib` to import all of Mathlib.

If you get stuck trying to solve a subgoal, try some of the following. Some of these may require Mathlib.

You are free to use tactics and commands that elicit suggestions from Lean, then call check_lean_code to get the suggestions. 
- `exact?` looks for tactics/theorems that exactly closes the current goal
- `apply?` looks for tactics/theorems that may be applicable to the current goal
- `rw?` looks for rewriting tactics that are applicable at the current goal. For example:
<example>
/-- The sum of first n numbers times 2 equals n * (n+1) -/
theorem sum_first_n_times_2 (n : ℕ) :
  2 * (∑ i in Finset.range n, (i + 1)) = n * (n + 1) := by
  induction n with
  | zero => simp
  | succ n ih =>
    simp [Finset.sum_range_succ]
    rw?

And Lean will return suggestions, including `rw [Nat.left_distrib]`
</example>

- `hint` tries every tactic registered via the register_hint tac command on the current goal, and reports which ones succeed
- If you know or guess the name of a theorem, you can use `#check` to print its type, e.g. `#check Nat.zero_add`.
- `#moogle` and `#leansearch` are two search engines that can take natural language queries and return relevant theorems and tactics in Mathlib. E.g. 
<example>
example : 3 ≤ 5 := by
  #moogle "If a natural number n is less than m, then the successor of n is less than the successor of m."
  sorry
</example>

You may also try the following tactics for closing goals, which might not have been in your training data:
- `aesop` searchs for a proof that closes the goal
- `omega` can close goals using integer and natural number arithmetic
- `simp_all` is a stronger version of `simp [*] at *` where the hypotheses and target are simplified multiple times until no simplification is applicable.
- `bv_decide` can close goals involving booleans and bit vectors
"""

SYSTEM_MESSAGE_OUTPUT="""When you have a final answer:
- If successful, output the final valid Lean code wrapped in <Result> tags
- If unsuccessful after {max_attempts} attempts, output "FAIL" followed by your best attempt wrapped in <Result> tags

Example successful output:
<Result>
theorem identity (P : Prop) : P → P :=
λ h =>  h
</Result>

Example failed output:
FAIL
<Result>
-- Best attempt, though it had errors:
theorem almost_right (P : Prop) : P → P :=
sorry  -- Could not complete proof
</Result>"""

def extract_imports(code: str):
    lines=code.splitlines(keepends=True)
    imports=[]
    rest=''
    for ln in lines:
        if ln.startswith('import'):
            imports.append(ln.split()[1])
        else:
            rest+=ln
    return imports, rest

def strip_reasoning(messages):
    return [{k:v for k,v in m.items() if k!='reasoning_content'} for m in messages]

class LeanFeatures:
    def __init__(self):
        self.sys_msg = SYSTEM_MESSAGE_FEATURES
    async def process(self, code, result):
        return result

class LoadSorry:
    def __init__(self):
        self.sys_msg = SYSTEM_MESSAGE_LOAD_SORRY
    async def process(self, code, result):

        if result['success'] and "sorry" in result['output']:
            from pantograph import Server
            imports, rest=extract_imports(code)
            server=await Server.create(imports=['Init']+imports, project_path=".")
            units =await server.load_sorry_async(rest)
            states = [ u.goal_state if u.goal_state is not None or len(u.messages)==0 else 'Error extracting goal state: '+'\n'.join(u.messages) for u in units]
            result['output'] += f"\nGoal States from sorrys:\n"+"\n\n".join([str(s) for s in states if s])
        return result


default_plugins=[LoadSorry(), LeanFeatures()]



async def interactive_lean_check(
    proof_request: str,
    model: str = models['sonnet'],
    temperature: float = 0.1,
    max_attempts: int = 5,
    final_check: bool = False,
    prefix: str ='',
    files =[],
    plugins = default_plugins,
    plain_text_mode = False,
    debug = False,
    messages=None,
    api_key: str = None
) -> Dict[str, Any]:
    """
    Interactively work with an LLM to generate valid Lean code, allowing for
    multiple attempts based on feedback.
    """
    if debug:
        litellm._turn_on_debug()

    if model in ['deepseek/deepseek-reasoner','gemini/gemini-2.0-flash-thinking-exp']:
        plain_text_mode=True
    SYSTEM_MESSAGE_INFO=SYSTEM_MESSAGE_TOOLS
    if plain_text_mode:
        SYSTEM_MESSAGE_INFO += SYSTEM_MESSAGE_PLAIN_TEXT
    for p in plugins:
        SYSTEM_MESSAGE_INFO += p.sys_msg
    if not messages: messages=[{"role": "system", "content": SYSTEM_MESSAGE_INFO+SYSTEM_MESSAGE_OUTPUT.format(max_attempts=max_attempts)}]
    elif SYSTEM_MESSAGE_INFO not in [m['content'] for m in messages]:
        sys_msgs = [m for m in messages if m['role']=='system']
        other_msgs=[m for m in messages if m['role']!='system']
        messages=sys_msgs+ [{"role": "system", "content": SYSTEM_MESSAGE_INFO}] +other_msgs

    msg=f"{proof_request}"
    if len(prefix)>0:
        msg+=f"\nThe following code is prepended to your code before execution by Lean. So when submitting your code via the tool call or final <Result> tag, only submit the part after this prefix:\n{prefix}"
    if files is not None and len(files)>0:
        for fn in files:
            with open(fn) as f:
                txt=f.read()
            messages.append({
                "role": "user",
                "content": f"The following is the conent of the file '{fn}':\n{txt}"
            })
        #prompt caching
        messages[-1]['cache_control']={'type': 'ephemeral'}
    messages = messages + [
        {"role": "user", "content": msg}
    ]
    
    tools = [create_lean_check_function()]
    tool_plugin={}
    for p in plugins:
        if hasattr(p, 'tool_def'):
            tools.append(p.tool_def())
            tool_plugin[p.tool_name] = p

    attempts = []
    try:
        supp_parallel=litellm.supports_parallel_function_calling(model=model) 
    except Exception as e:
        print (e)
        supp_parallel=False
    for attempt in range(max_attempts+1):

        try:
            kwa={}
            if not plain_text_mode:
                kwa['tools']=tools
            if api_key:
                kwa['api_key']=api_key
            if model == 'o3-mini-high':
                model='o3-mini'
                kwa['reasoning_effort']='high'
            if supp_parallel and model not in ['o3-mini', 'o1']:
                kwa['parallel_tool_calls']=False
            if model not in ['o3-mini']:
                kwa['temperature']=temperature
            response = await acompletion(
                model=model,
                messages=strip_reasoning(messages),
                **kwa
            )
            
            # Check if we have a final result

            message = response.choices[0].message
            if not message:
                return {
                    "success":False,
                    "attempts":attempts,
                    "error":response.choices[0].finish_reason,
                    "messages":messages
                }
            message_content = message.content if hasattr(message, 'content') else None
            function_call = message.tool_calls[0] if hasattr(message, 'tool_calls') and message.tool_calls else None
            if message_content and "<Result>" in message_content:
                # Extract the final result
                match = re.search(r"<Result>(.*?)</Result>", message_content, re.DOTALL)
                if match:
                    final_code = match.group(1).strip()
                    final_code = final_code.replace("```lean", "").replace("```", "")
                    if final_check:
                      # Verify the final code works
                      final_result = await check_lean_code(final_code)
                      attempts.append({
                        "code": prefix+final_code,
                        "result": final_result,
                        "is_final": True
                      })
                    messages.append(message.model_dump())
                    if "FAIL" in message_content:
                        success=False
                    else:
                        success=final_result["success"] if final_check else True

                    return {
                        "success": success,
                        "attempts": attempts,
                        "final_code": final_code,
                        "messages": messages
                    }
            
            # If we have a function call, execute it and continue the conversation
            if function_call or (plain_text_mode and message_content and '<Try>' in message_content):
                if function_call:
                    args = json.loads(function_call.function.arguments)
                else:
                    match = re.search(r"<Try>(.*?)</Try>", message_content, re.DOTALL)

                    args = {'code': match.group(1).strip()}
                if (function_call and function_call.function.name == 'check_lean_code') or plain_text_mode:
                  result = await check_lean_code(
                    code=prefix+args["code"],
                    json_output=args.get("json_output", False),
                    plugins=plugins
                  )
                
                  attempts.append({
                    "code": args["code"],
                    "result": result,
                    "thought": message_content,
                    "is_final": False
                  })
                else:
                  p=tool_plugin.get(function_call.function.name)
                  if p:
                    result = await p.tool_function(**args)

                # Add the result to the conversation
                messages.append(message.model_dump())
                #{
                #    "role": "assistant",
                #    "content": None,
                #    "function_call": {
                #        "name": "check_lean_code",
                #        "arguments": json.dumps(args)
                #    }
                #})
                if plain_text_mode:
                  output=f"Given your code, Lean outputs the following:\n{result['output']}"
                  if result['error']:
                    output+=f"\nError message:\n{result['error']}"
                  messages.append({
                    "role": "user",
                    "content": output 
                  })
                else:
                  messages.append({
                    "tool_call_id": message.tool_calls[0].id,
                    "role": "tool",
                    "name": function_call.function.name,
                    "content": json.dumps(result)
                  })
                
                continue
            
            # If we get here without a Result tag or function call, add the response
            # to continue the conversation
            messages.append({
                "role": "assistant",
                "content": message_content
            })
            if 'anthropic' in model:
                return {
                        "success": False,
                        "attempts": attempts,
                        "messages": messages
                }
            else:
                tool_ins="Enclose your code in <Try> </Try> tags" if plain_text_mode else "Call the provided tool" 
                messages.append({
                    'role': 'user',
                    'content': f"To try your code with Lean, {tool_ins}. To finish with the final answer, enclose your final code with <Result> </Result>."
                })
        except Exception as e:
            attempts.append({
                "error": str(e) + '\n' + traceback.format_exc(),
                "is_final": False
            })
            await asyncio.sleep(1)
        if 'anthropic' in model:
            await asyncio.sleep(1)
    # If we've exhausted attempts, return the history
    return {
        "success": False,
        "attempts": attempts,
        "error": f"Failed to get valid result after {max_attempts} attempts",
        "messages": messages
    }

def create_lean_check_function() -> Dict[str, Any]:
    """
    Creates the function definition for LLM function calling.
    Returns a dictionary describing the function that can be passed to LLMs.
    """
    return {
      "type": "function",
      "function":{
        "name": "check_lean_code",
        "description": "Checks Lean 4 code using the Lean 4 proof assistant",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Lean 4 code to check"
                },
                "json_output": {
                    "type": "boolean",
                    "description": "Whether to get Lean's output in JSON format. If omitted, defaults to False"
                }
            },
            "required": ["code"]
        }
      }
    }


async def check_lean_code(code: str, json_output: bool = False, plugins = default_plugins) -> Dict[str, Any]:
    """
    Sends code to the Lean executable and returns the results.
    
    Args:
        code: Lean code to check
        json_output: Whether to get output in JSON format
        
    Returns:
        Dictionary containing:
            - success: bool indicating if code checked successfully
            - output: string or parsed JSON containing Lean's output
            - error: string containing error message if any
    """
    try:
        # Create temporary file for the Lean code
        with tempfile.NamedTemporaryFile(suffix='.lean', mode='w', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name
        
        # Prepare command with optional JSON flag
        cmd = ['lake', 'env', 'lean']
        if json_output:
            cmd.append('--json')
        cmd.append(temp_file_path)
        
        # Run Lean on the temporary file
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        # Process the output
        success = result.returncode == 0
        output = result.stdout
        
        # Parse JSON output if requested and available
        if json_output and output:
            try:
                output = json.loads(output)
            except json.JSONDecodeError as err:
                print(f"Failed to parse Lean JSON output: {err}.\n Keeping output as string.")
        result = {
            "success": success,
            "output": output,
            "error": result.stderr if not success else None
        }
        for p in plugins:
            if hasattr(p, 'process'):
                result=await p.process(code, result)
        return result

    except subprocess.CalledProcessError as e:
        raise LeanToolException(f"Error running Lean: {str(e)}")
    except Exception as e:
        raise LeanToolException(f"Unexpected error: {str(e)}")


async def main(query):
    result = await interactive_lean_check(
        query,
        model=models['sonnet'],
        temperature=0.1,
        max_attempts=5
    )
    
    print("Success:", result["success"])
    print("Number of attempts:", len(result["attempts"]))
    
    if result["success"]:
        print("\nFinal code:")
        print(result["final_code"])
    else:
        print("\nFailed to get valid code. Best attempt:")
        print(result["attempts"][-1])
        
    print("\nFull interaction history:")
    for i, attempt in enumerate(result["attempts"], 1):
        print(f"\nAttempt {i}:")
        if 'code' in attempt: print(attempt["code"])
        elif 'error' in attempt:
                print("Error:", attempt["error"])
        if "result" in attempt:
            print("Result:", attempt["result"])


if __name__=='__main__':
  asyncio.run(main(sys.argv[1:]))
