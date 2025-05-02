import Lean.Elab.Command
import Lean.Meta.Eval
import Plausible.Gen
import Plausible.Sampleable
 

open Plausible


open SampleableExt

/--
Print (at most) 10 samples of a given type to stdout for debugging.
-/
def printSamples2 {t : Type u} [Repr t] (g : Gen t) : IO PUnit := do
-- TODO: this should be a global instance
  letI : MonadLift Id IO := ⟨fun f => pure <| Id.run f⟩
  do
    -- we can't convert directly from `Rand (List t)` to `RandT IO (List Std.Format)`
    -- (and `RandT IO (List t)` isn't type-correct without
    -- https://github.com/leanprover/lean4/issues/3011), so go via an intermediate
    let xs : List Std.Format ← Plausible.runRand <| Rand.down <| do
      let xs : List t ← (List.range 10).mapM (ReaderT.run g ∘ ULift.up)
      pure <| ULift.up (xs.map repr)
    for x in xs do
      IO.println s!"{x}\n"


open Lean Meta Elab

private def mkGenerator (e : Expr) : MetaM (Level × Expr × Expr × Expr) := do
  let exprTyp ← inferType e
  let .sort u ← whnf (← inferType exprTyp) | throwError m!"{exprTyp} is not a type"
  let .succ u := u | throwError m!"{exprTyp} is not a type with computational content"
  match_expr exprTyp with
  | Gen α =>
    let reprInst ← synthInstance (mkApp (mkConst ``Repr [u]) α)
    return ⟨u, α, reprInst, e⟩
  | _ =>
    let v ← mkFreshLevelMVar
    let sampleableExtInst ← synthInstance (mkApp (mkConst ``SampleableExt [u, v]) e)
    let v ← instantiateLevelMVars v
    let reprInst := mkApp2 (mkConst ``SampleableExt.proxyRepr [u, v]) e sampleableExtInst
    let gen := mkApp2 (mkConst ``SampleableExt.sample [u, v]) e sampleableExtInst
    let typ := mkApp2 (mkConst ``SampleableExt.proxy [u, v]) e sampleableExtInst
    return ⟨v, typ, reprInst, gen⟩



elab "#samplenl " e:term : command =>
  Command.runTermElabM fun _ => do
    let e ← Elab.Term.elabTermAndSynthesize e none
    let ⟨u, α, repr, gen⟩ ← mkGenerator e
    let printSamples := mkApp3 (mkConst ``printSamples2 [u]) α repr gen
    let code ← unsafe evalExpr (IO PUnit) (mkApp (mkConst ``IO) (mkConst ``PUnit [1])) printSamples
    _ ← code

