

# Available utilities

- MCP tool that takes Lean 4 source code and checks it with the Lean executable
- pbtdp.py: command-line script, takes a filename containing Lean source code and a function signature, generate sample inputs and evaluates the function on those inputs.
  Usage: `poetry run python pbtdp.py <filename> <function signature> [--num_test=N]`

# Development workflow for Lean 4 with dependent types and proofs

1. **MCP tool usage**
   - Use `mcp__LeanTool__check_lean` to validate Lean syntax and extract proof goals from `sorry` statements
   - Analyze the proof goals to understand what needs to be proven for each `sorry`
   - Make sure runtime checks (using `checkRes` and `IO.println` error messages) match corresponding proof goals

2. **Property-based testing with pbtdp.py**
   - Pass the complete function signature including proof arguments:
     ```
     poetry run python pbtdp.py <filename> "<function> (arg1: Type1) (arg2: Type2) (proof1: P1) (proof2: P2)" --num_test=N
     ```
   - The script handles generating test cases and proof terms for the arguments
   - Default is 5 test cases, increase with `--num_test=N` for better coverage
   - Results show passed/failed/unknown tests and details of any failures
   - The script detects both standard Lean errors and custom "failed check:" messages

3. **Process for finding and fixing mismatches**
   - Compare runtime checks (using `checkRes:Bool`) with the proof goals shown by MCP tool
   - Make sure runtime checks test exactly the same conditions as proof goals
   - Re-verify using the MCP tool after making changes
   - Run property-based testing with increased test cases to confirm correctness

4. **Runtime verification pattern**
   ```lean
   let checkRes:Bool := condition_matching_proof_goal
   if !checkRes then
     IO.println "failed check: [exact condition being tested]"
   return ResultType (by sorry)
   ```

5. **Best practices**
   - Runtime checks should exactly match the proof goals from sorries
   - Error messages should clearly indicate what condition failed
   - Increase test cases when needed to ensure coverage of all code paths
   - When using dependent types, include all proof arguments in testing signatures
