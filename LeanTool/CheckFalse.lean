import Lean

open Lean Elab Tactic Meta

/-- 
Tactic that checks whether the current goal is false by attempting to prove its negation.
If the negation is provable, reports an error with the proof.
Otherwise, acts like `sorry` (admits the goal without proof).

This tactic only operates on the main goal. Other goals remain unchanged.

This is useful for debugging and checking the plausibility of goals, similar to the `plausible` tactic.

Usage:
- `check_false` (uses `grind` by default)
- `check_false simp` (uses `simp` tactic)
- `check_false omega` (uses `omega` tactic)
-/
syntax "check_false" (ppSpace tacticSeq)? : tactic

elab_rules : tactic
| `(tactic| check_false $[$tac]?) => do
  -- Get all current goals
  let allGoals ← getGoals
  if allGoals.isEmpty then
    throwError "check_false: no goals to check"
  
  -- Work with the main goal
  let mainGoal := allGoals.head!
  let otherGoals := allGoals.tail!
  
  let goalType ← mainGoal.getType
  let negGoalType ← mkAppM ``Not #[goalType]
  
  -- Get the tactic to use (default to hammer)
  let tacticToUse ← match tac with
    | some t => pure t
    | none => `(tacticSeq| grind)
  
  -- Create a new goal for ¬(original goal)
  let negGoal ← mkFreshExprMVar negGoalType
  let negGoalMVarId := negGoal.mvarId!
  
  -- Try to prove the negation using the specified tactic
  setGoals [negGoalMVarId]
  
  try
    evalTactic tacticToUse
  catch e =>
    -- Tactic failed to prove negation (actual failure), act like sorry on main goal
    let sorryProof ← mkSorry goalType (synthetic := true)
    mainGoal.assign sorryProof
    setGoals otherGoals
    logInfo m!"Failed to prove negation (tactic error: {e.toMessageData}); acting like 'sorry' on main goal"
    return
  
  -- Check if the negation goal was actually solved
  let remainingGoals ← getGoals
  if remainingGoals.isEmpty then
    -- Successfully proved the negation!
    let negProof ← instantiateMVars negGoal
    
    -- Restore original goal state before erroring
    setGoals allGoals
    throwError m!"Goal is false! Proof of negation:\n{negProof}\n\nThe goal `{goalType}` can be disproven."
  else
    -- Negation wasn't fully proved, act like sorry on main goal
    let sorryProof ← mkSorry goalType (synthetic := true)
    mainGoal.assign sorryProof
    setGoals otherGoals
    logInfo m!"Could not prove negation of goal; acting like 'sorry' on main goal"
