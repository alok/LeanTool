---
layout: post
title:  "Property-Based Testing with Dependent Types: Experiment Alpha-Beta"
date:   2025-03-28 07:30:00 +0000
categories: AI
---

(This also serves as progress report #4 of our [overall program](https://gasstationmanager.github.io/ai/2024/11/04/a-proposal.html).)

---

## Miscellaneous Updates

It's been a while since our last update. Progress has slowed down mainly because I got very busy at work. Nevertheless, in this post I'll show a glimpse of an idea I've been developing that I believe can become very potent. Before diving into our main topic, let me mention a couple of other updates.

- **LeanTool with MCP**. [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) has become a standard for exposing functionalities to the LLM, with adoption by multiple vendors.
[LeanTool](https://github.com/GasStationManager/LeanTool) now supports MCP as one of its modes of deployment. 
How it works: the Lean execution tool (and plugins including load_sorry) is exposed as a MCP tool in a MCP server,
which apps (like Cursor) can then make available to LLMs to use.
The main difference with earlier modes of LeanTool as library function and API server 
is that here the MCP server is just the Lean execution part, so no LLM, and no feedback loop.
So the app needs to connect to the LLM and manage the  feedback loop.
Many modern coding assistant apps are capable of doing that. LeanTool's MCP mode has been tested to work with Cursor, Claude Code and Goose. The upcoming VS Code Insiders edition will have a GitHub Copilot agent mode that also supports MCP.


## Property-Based Testing with Dependent Types

I would like to develop further an idea I mentioned briefly in a [previous post](https://gasstationmanager.github.io/ai/2025/01/22/hallucination.html#2-tools-and-approaches).


This is in the context of our [hallucination detection and recovery](https://gasstationmanager.github.io/ai/2025/01/22/hallucination.html) effort. At a high level, our goal is to output correct code. Our challenge is that LLMs hallucinate. We want to leverage formal specs and ITPs as tools to detect and recover from hallucinations.

In a series of posts ([1](https://gasstationmanager.github.io/ai/2025/01/22/hallucination.html), [2](https://gasstationmanager.github.io/ai/2025/02/05/hallucination-followup.html), [3](https://gasstationmanager.github.io/ai/2025/02/18/fvapps.html)), we developed tools that combined property-based testing (PBT) and automated theorem proving (ATP), and showed that they are effective at detecting the presence of hallucinations.

Going from recognition (detecting the presense) to locating and fixing the bug can be nontrivial, especially as the tasks become more complex.
At a high level, this can be seen as a credit assignment problem.

We propose the following approach, that draws ideas from both  type-driven and test-driven development. 
- As in my [previous](https://gasstationmanager.github.io/ai/2024/12/03/memoization1.html) [posts](https://gasstationmanager.github.io/ai/2024/12/09/dp2.html) on programming with dependent types,
we annotate data with logical properties that the data should satisfy, encoded as type information.

- This includes but is not limited to subtyping the return values of functions with their postconditions.

- This naturally results in proof goals inside of the implementation.  Initially, we can put `sorry`s in place of the required proofs.

- Before attempting the proofs, we want to first ensure that the implementation is correct. We apply property-based testing (PBT) to test whether there are counterexamples to these proof goals

- If counterexample found: we have detected hallucination. So the implmentation of this subgoal is wrong. We either need to fix the implementation so that it satisfies the subgoal, or adjust the subgoal so that it can be satisfied while still sufficient to lead to the final solution,
or to find a different path towards the solution that no longer invovles this subgoal. 

- We also test the entire function with PBT.

- Finally, we have an implementation that we believe to be correct, because the function and its parts have passed PBT.

- We have reached our original goal of outputting correct code. Can we go one step further
and prove the correctness of the code, i.e. filling the sorries? 
Because each of these are relatively simple, and implementation likely correct, these can hopefully be dispatched by ATP, eg. tactics like `simp`, `omega`, `linarith`.
Otherwise: ask LLM to generalize from examples, devise an informal proof, convert to a formal proof sketch with sorries for subgoals, (optionally checking the subgoals with PBT), try dispatching the sorries with ATP, recurse.


Why do I think this approach is promising?
- At a high level, our goal is effective use of feedback from the interactive theorem prover (Lean), to guide the LLM towards correct solutions.
Broadly, denser feedback (more signals) is better than sparser feedback.
Also, more immediate feedback is better than delayed feedback, because the former helps with credit assignment.
The proposed approach is designed to provide opportunities for dense, immediate feedback from Lean and its features.
- Why PBT (instead of directly attempting proofs): a failed attempted proof is a very weak signal. LLMs are currently not very strong at proving compared to coding. Also LLMs don't have a good understanding of proofs in Lean.
So: very hard to discern whether the failed attempt is due to lack of proof ability or wrong implementation. On the other hand, LLMs understand testing much better.
- Also, this gets us more than half way towards producing the proof of correctness.

## Towards a Miniumn Working Example

Let's work this out on a specific coding task. 
I am going to do one of my favorite algorithms. 
Let me hype it up by engaging in some trash talking: kids today chanting about "inference-time scaling laws", perhaps can learn a thing or two from the classics. 
To get milage out of inference-time compute, you need more than just scaling up the compute. 
The search space is vast, you will hit a wall very quickly. How did the classical AI guys create Deep Blue, able to beat Garry Kasparov? Contrary to popular accounts, it was not just by "brute-force" search. One of the ingredients of the solution was a beautiful search algorithm that helps cut through the exponential search space. 

Today, we are going to implement Alpha-Beta Pruning.

Is this too easy for LLMs? Since Alpha-Beta Pruning is reasonably well-known and most likely in the training sets of the LLMs, can LLMs already produce correct implementations of it?
Anecdote time! In the early days of GTP 4, when the meme of the day was "GPT can't play chess", I prompted GPT 4 to create a chess-playing program by implementing alpha-beta pruning as the search algorithm, 
using the python-chess library for move generation. For evaluation function, I asked GPT for suggestions and it created one based on static values of pieces plus "piece-square tables", which are bonuses based on the squares the pieces are at. It was able to play a solid game of chess, and I had quite a few enjoyable games against it.
On the other hand, GPT 4 did hallucinate during the implementation and I had to do quite a bit of debugging to correct it. One tricky aspect of implementing alpha-beta is that the existing online code that ends up in training sets fall into two different set ups: one is the min-max set up where one player is minimizing and the other player is maximizing the values, so the algorithm divides into the min-node case and the max-node case. 
The other is the nega-max set up where both players are maximizing, just the signs of the values are flipped when going from one level to the next. Both are correct ways of implementing, as long as the programmer is consistent. GPT 4 was not always consistent. 

In preliminary experiments with current LLMs in Lean, this failure mode still exists when trying to implement alpha-beta. 
So this is a good level of hardness: the algorithm is understood by LLMs at an informal level, 
but there are pitfalls of implementation that they could fall into. This is exactly whre hallucination detection can help.


### The specification

We start by developing a formal specification. First, we define a GameTree
as either a terminal node with an Int value,
or a List of GameTrees.
We are going to interpret the value of the terminal node to be the value from the perspective of the player to move. The game is alternating-moves, so we switch player when we go down each level of the tree. 

We also introduce a parameter `maxV` so that the values in the GameTree falls between `-maxV` and `maxV`.

```
import Plausible
import Std
open Plausible

abbrev PosInt :={x:Int // x>0}

inductive GameTree (maxV: PosInt)  where
|terminal  (value: Int) (pmin:value>= -maxV)(pmax:value<=maxV)
|node (children: List (GameTree maxV))
deriving Repr
```

Next, we need to define what is the *value* of a game tree, i.e. 
the value of the root node when both players are playing an optimal strategy.
We define it to be the result of the following minimax algorithm.
Note that we are going with the nega-max set up. 

```
def minimax: (game: (GameTree maxV)) -> Int
|GameTree.terminal v _ _ => v
|GameTree.node [] => -maxV
|GameTree.node (child::tail) =>
    let r:= - minimax child
    max r (minimax (GameTree.node tail))
termination_by game => game
```
(For simplicity, we are skipping over concepts like subgame-perfect equilibrium since they are orthogonal to the purpose of this post.)

Next, we want to define the signature of the alpha-beta pruning algorithm,
and then the specification that the algorithm returns the correct value of the game tree.
Before diving into the formal definitions, let's think about it informally.
At a high level, alpha-beta takes in as arguments a GameTree, and two Ints `alpha` and `beta`.
It has a contract saying that if the value of the GameTree is between alpha and beta, then the function is supposed to compute the exact value. If the value of the GameTree is less or equal to alpha or greater or equal to beta, then the function does not need to return the exact value,
only need to return alpha (as an upper bound) or beta (as a lower bound), respectively. 

So traditionally the return value of alpha-beta would be an Int, that could be either alpha, beta, or the actual value of the GameTree. 
For our exercise, we are going to annotate the return value with additional type information that encodes the postcondition. Normally it is done via subtyping. Here, it becomes clear that the return value falls into three distinct cases, as upper bound (alpha), lower bound (beta), or exact value. A natural way to represent this in Lean is as an inductive type with three constructors.

```
inductive ABResult(g: GameTree maxV) (alpha beta: Int) where
|lb (p: beta <= minimax g) --when beta is a lower bound of the real minimax value
|ub (p: alpha >= minimax g) --when alpha is an upper bound of the real minimax value
|value (x:Int) (p: x=minimax g)
```

We can then define the signature of the alpha-beta function as
```
def alphabeta (g: GameTree maxV) (alpha beta: Int)
(pa: alpha >= - maxV.val) (pb: beta<=maxV.val)
: ABResult g alpha beta
```
Now that we have encoded the specification in the return type, an implementation of this function
that type-checks is also a correct implementation.

(We also need a main driver function that makes the initial call to `alphabeta`
with `alpha` as `-maxV` and `beta` as `maxV`. Its implementation and proof of correctness is left as exercise to the reader.)

### Generating example inputs

One more thing before we dive into implementation. Since we will be doing property-based testing,
we need a way to generate random examples of input arguments. Built-in types like Int (for alpha and beta) are generally automatically covered by the property-based testing library (Plausible for Lean). But GameTree is a user-defined type, and it falls to us to specify how to generate random examples of GameTrees.

For Plausible, this involves defining instances of the type classes Shinkable and SampleableExt.
The following is my implementation. I won't go into the details; I refer interested readers to the documentations of Plausible. With this, now Plausible is able to generate randome examples of GameTrees.

```
instance: Shrinkable (GameTree maxV) where
  shrink t := match t with
  |GameTree.terminal x _ _ => []
  |GameTree.node [] => []
  |GameTree.node (h::tail) => [GameTree.node tail]

instance: SampleableExt (GameTree maxV):=
SampleableExt.mkSelfContained do
let rec helper (level:Nat) : Gen (GameTree maxV):= do
  let isTerm← SampleableExt.interpSample Bool
  if level=0 ∨  isTerm then
    let x← SampleableExt.interpSample Int
    let x' := min x maxV
    let x'' := max x' (-maxV)
    return GameTree.terminal x'' (by omega) (by omega)
  else
    let isNil ← SampleableExt.interpSample Bool
    if isNil then
      return GameTree.node []
    else
      let ch ← Gen.listOf do helper (level-1)
      return GameTree.node ch
let sz ← Gen.getSize
let lsz := Nat.log2 sz
let nl ← Gen.choose Nat 0 lsz (by omega)
helper nl


instance : SampleableExt PosInt:=
SampleableExt.mkSelfContained do
  let x ← Gen.chooseNat
  return ⟨ x+1, by omega⟩
```
Now `#sample GameTree ⟨ 4, by omega ⟩` will generate and print 10 random examples of GameTrees.

I believe it is a good exercise to do some form of this, i.e. generating examples, as part of the development of the specification. 
Because this can be an effective way to debug the specification. 
The way it is currently set up, we are assured that when the implementation type-checks, 
it is correct according to the specification; but did we create any bugs in the specification?
For our current task, creating examples allows us to check that our GameTree type definition is reasonable, and that instances of GameTree can be passed to minimax and return  reasonable answers.


### Implementation
Let's dive into the implementation. The first natural thing to do is to split into cases on the input GameTree. We want to mostly follow the recursive structure of minimax, deviating only when necessary. Experience suggests that this will make proofs easier.
```
def alphabeta (g: GameTree maxV) (alpha beta: Int)
(pa: alpha >= - maxV.val) (pb: beta<=maxV.val)
: ABResult g alpha beta
:= match g with
|GameTree.terminal x _ _=> sorry
|GameTree.node [] => sorry
|GameTree.node (child::tail) => sorry
```

The next natural thing to do is to utilize the Plausible library now that we are able to generate input GameTrees. Specifically, as we implement branches of the logic, call `plausible` on the proof goals:
```
def alphabeta (g: GameTree maxV) (alpha beta: Int)
(pa: alpha >= - maxV.val) (pb: beta<=maxV.val)
: ABResult g alpha beta
:= match g with
|GameTree.terminal x _ _=> ABResult.value x (by plausible)
|GameTree.node [] => sorry
|GameTree.node (child::tail) => sorry
```
This is then supposed to do property-based testing on the subgoal, i.e. generating random inputs
and checking whether the subgoal is satisfied.
However, `plausible` quite often was not able to run. The error messages were hard to decipher;
one hypothesis is that perhaps all the `sorry`s in the code is interferring with its reasoning.

For now, one workaround is to do things more manually: just do the same checks that `plausible` would have done, but via print-debugging. For Lean, printing to the output is to be done with the IO monad.
So for this stage of the development, we change the output type to include the IO monad.

Still, Lean will not `#eval` a function if it contains `sorry`s. To make this work,
we can use `#eval!`, but
we will need to make sure the function's implmentation is complete; only the proofs may contain `sorry`s. 
As we are growing the function step by step, this may entail temporarily creating stubs of implementation for certain branches, i.e. implmentations that return the correct type (minus certain proof goals which can be `sorry`s) but are known to be not correct. 
One issue is that these stubs may interfere with property-based testing in other branches, 
especially since the function is recursive.
So let's make a rule: when we create a stub in a branch, we always guard it by property-based
testing (in this case, via printing). 

Let us fast forward a little bit, since the first two base cases have obvious correct solutions that matches what `minimax` does, and have simple proofs (`simp[minimax]` which plugs in the definition of `minimax` and simplifies).
Let us focus on the main case, starting with a stub for implementation.

```
def alphabeta (g: GameTree maxV) (alpha beta: Int)
(pa: alpha >= - maxV.val) (pb: beta<=maxV.val)
: IO <| ABResult g alpha beta :=do
match g with
|GameTree.terminal x _ _=> return ABResult.value x (by simp[minimax])
|GameTree.node [] => return ABResult.value (-maxV) (by simp[minimax])
|GameTree.node (child::tail) => return ABResult.ub (by sorry)
```
The next step is to get the proof goal corresponding to the `sorry`.
In a Lean IDE environment (VSCode or the web editor) we can hover before the `sorry` to see
the proof goal. In an automated workflow we can utilize e.g. the load_sorry plugin of LeanTool.
In this case, the proof goal is `alpha ≥ minimax (GameTree.node (child :: tail))`.
In lieu of `plausible`, we evaluate this condition and print an error if it fails:

```
def alphabeta (g: GameTree maxV)(alpha beta: Int)
(pa: alpha >= - maxV.val) (pb: beta<=maxV.val)
: IO <| ABResult g alpha beta :=do
match g with
|GameTree.terminal x _ _=>return ABResult.value x (by simp[minimax])
|GameTree.node [] => return ABResult.value (-maxV) (by simp[minimax])
|GameTree.node (child::tail) =>
  let testRes:Bool := alpha ≥ minimax (GameTree.node (child :: tail))
  if !testRes then
    IO.println "failed check: alpha ≥ minimax (GameTree.node (child :: tail))"
  return ABResult.ub (by sorry)

def g1:GameTree ⟨ 3, by decide⟩ := GameTree.node [GameTree.terminal 1 (by decide) (by decide)]
#eval! alphabeta g1 (-2) 2  (by decide) (by decide)
```

Testing the function with the above example will catch the failed check with error message printed out as expected.

It may be reasonable to raise an exception after the failed check. Ultimately it boils down to what is more helpful to the LLM.

For the next step, we replace the stub with something closer to being correct. In our case, we are going to recursively call alphabeta on the first child, and inspect the result. 
This is where the alpha-beta algorithm differs from minimax:
whereas in minimax all of the children are processed no matter what, 
in alpha-beta we look at the results for each child, and decide whether to skip the rest 
of the list of children, i.e. prune.

We create stubs for each of the three cases of the return value of the recursive alphabeta call,
and guard them with the checks on the extracted proof goals, as before.
```
def alphabeta (g: GameTree maxV)(alpha beta: Int)
(pa: alpha >= - maxV.val) (pb: beta<=maxV.val)
: IO <| ABResult g alpha beta :=do
match g with
|GameTree.terminal x _ _=>return ABResult.value x (by simp[minimax])
|GameTree.node [] => return ABResult.value (-maxV) (by simp[minimax])
|GameTree.node (child::tail) =>
  let r ←   alphabeta child (-beta) (-alpha) (by omega) (by omega)
  match r with
  |ABResult.value x prf =>
    let candidate := -x
    let checkRes:Bool:=candidate = minimax (GameTree.node (child :: tail))
    if !checkRes then
      IO.println "failed check: candidate = minimax (GameTree.node (child :: tail))"
    return ABResult.value candidate (by sorry)
  |ABResult.lb prf=>
    let checkRes:Bool:=alpha ≥ minimax (GameTree.node (child :: tail))
    if !checkRes then
      IO.println "failed check: alpha ≥ minimax (GameTree.node (child :: tail))"
    return ABResult.ub (by sorry)
  |ABResult.ub prf=>
    let checkRes:Bool:=beta ≤ minimax (GameTree.node (child :: tail))
    if !checkRes then
      IO.println "failed check: beta ≤ minimax (GameTree.node (child :: tail))"
    return ABResult.lb (by sorry)

def g2:GameTree ⟨ 3, by decide⟩ := GameTree.node [GameTree.terminal 1 (by decide) (by decide), GameTree.terminal 0 (by decide) (by decide)]
#eval! alphabeta g2 (-3) 3  (by decide) (by decide)
```
Testing with the above example, it prints `failed check: candidate = minimax (GameTree.node (child :: tail))`, which correctly catches that the corresponding stub implementation for that case is wrong.


### Next Steps

We can progress further by incrementally implementing more of the function, guarded by property-based tests. But let us leave it for the next installment, when we try it with an LLM.

For now, hopefully you got a flavor of this workflow. Observe that the subgoals and the corresponding tests can be automatically generated. The programmer can focus on implementing the subgoals, and responding to any failed checks.

What do we need to implement before we are ready to try it with an LLM?
- We need a script that, given the function signature, generate random example inputs (say with #sample), and call the function on these examples with #eval!.
Our PBT script from our WakingUp experiment has most of what we need, but needs to be adapted and made more robust.
- We need a feedback loop so that the LLM can iteratively improve the implementaion and get help from PBT each step of the way. We have LeanTool; we need a PBT plugin to LeanTool. 
- Some of the subtasks, like extracting the proof goals and turning them into property based tests, are ideally done automatically; if that turns out to be hard to implement, an option is to prompt the LLM to do this part, ie. inserting the print statements.

As always, comments and suggestions are welcome! If you are interested in collaborating, let me know!
