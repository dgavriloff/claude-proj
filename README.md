# The Roads Not Taken

## Classic Computing Ideas, Rebuilt

> "The best way to predict the future is to invent it." — Alan Kay

This repository contains working implementations of the most ambitious ideas
from computing's golden age — ideas that were conceived before the industry
got distracted by quarterly earnings, walled gardens, and engagement metrics.

Each module is a love letter to a specific pioneer and their vision:

### The Systems

| Module | Pioneer | Year | Big Idea |
|--------|---------|------|----------|
| `memex/` | Vannevar Bush | 1945 | Associative trails through knowledge — not folders, not search, but *trails* |
| `xanadu/` | Ted Nelson | 1960 | Bidirectional links, transclusion, version permanence — what the web should have been |
| `nls/` | Doug Engelbart | 1962 | Augmenting human intellect through structured, multi-view documents |
| `dynabook/` | Alan Kay | 1972 | A live object environment where everything is inspectable and modifiable |
| `symbiosis/` | J.C.R. Licklider | 1960 | Human-computer thinking as *symbiosis*, not automation |
| `sketchpad/` | Ivan Sutherland | 1963 | Constraint-based drawing — declare relationships, the computer solves positions |
| `planner/` | Carl Hewitt | 1969 | Goal-directed reasoning — state what you want, the system figures out how |
| `logo/` | Seymour Papert | 1967 | Embodied mathematics — the turtle as "an object to think with" |
| `ipl/` | Newell, Shaw, Simon | 1956 | The first list processor and theorem prover — before LISP existed |

### The Unified System

`pioneer.py` — A unified interface that connects all nine systems together,
demonstrating what computing might look like if we'd followed these threads
instead of the ones we did.

### What Went Wrong

These ideas were marginalized not because they failed, but because they
didn't fit the business models that emerged:

- **Bush's trails** became Google's PageRank — useful, but missing the personal, associative element
- **Nelson's transclusion** became copy-paste — destroying attribution and the link economy
- **Engelbart's augmentation** became PowerPoint — a tool for presentation, not thought
- **Kay's Dynabook** became the iPad — a consumption device, not a creation medium
- **Licklider's symbiosis** became... well, we're still waiting
- **Sutherland's constraints** became CAD — powerful but imprisoned in specialized tools
- **Hewitt's PLANNER** became Prolog — then was buried by the AI Winter
- **Papert's LOGO** became "computer literacy" — typing tests instead of mathematical exploration
- **Newell & Simon's IPL** became LISP — which survives, but mostly in Emacs configs

### Running

```python
from pioneer import Pioneer

p = Pioneer()
p.demo()
```

### Philosophy

Every line of code in this repository is annotated with quotes from the
original papers and books. Read the docstrings. They're the point.

The code is the medium, but the ideas are the message.
