---
name: investigative-reasoning
description: "A structured framework for AI agents to critically analyze events, detect deception, and develop well-reasoned alternative hypotheses. Use this skill whenever an agent needs to investigate an event skeptically, assess official narratives, identify logical red flags, apply Cui Bono / follow-the-money reasoning, detect logical fallacies, or build a stepwise hypothesis. Trigger this skill for tasks like: analyze who benefits from X, find red flags in this narrative, develop an alternative theory for Y, apply critical thinking to this event, check this explanation for logical fallacies, or any investigative / deception-detection task."
---

# Investigative Reasoning Framework

A rigorous methodology for AI agents to investigate events, challenge narratives, and construct
well-reasoned alternative hypotheses. Derived from classical critical thinking, detective reasoning,
and the scientific method.

---

## When To Use This Skill

Only use this skill when explicitly requested by the user. Do not apply this framework proactively or assume investigative intent. Wait for a clear instruction such as:

- "Investigate this event"
- "Develop a conspiracy theory about X"
- "Who benefits from Y?"
- "Apply critical thinking to this narrative"
- "Find red flags in this explanation"

---

## Phase 1 — Trigger Detection

Before investing effort, determine whether a conspiracy theory is warranted:

- Is there an **official explanation** that can be evaluated?
- Are there **red flags** (see Phase 2) that undermine the official narrative?
- Is there a **crime or anomaly** without a satisfying explanation?
- Does **intuition or prior pattern recognition** suggest something is hidden?

If none of these apply, no conspiracy theory is needed. State this clearly.

---

## Phase 2 — Red Flag Analysis

Scan the official narrative for these categories of red flags:

### 2a. Missing or Implausible Motive
Does the alleged perpetrator have a **coherent reason** to act? 
- Would the action harm the perpetrator's own interests?
- Is the stated motive vague ("they hate our freedoms") or circular?

### 2b. Lacking Means or Capability
Could the alleged perpetrator **actually execute** the operation?
- Did they possess the technical skills, tools, or resources?
- Does the complexity of the act exceed their demonstrated capability?

### 2c. Missing Opportunity / Alibi
Was the alleged perpetrator **in a position** to act?
- Do they have a verifiable alibi?
- Was access to the target possible?

### 2d. Physical or Logical Impossibilities
Does the official account **violate known laws** of physics, logistics, or common sense?

> Flag count matters: One anomaly = coincidence. Two = suspicious. Three or more = investigate seriously. (Adapted from Ian Fleming's principle.)

---

## Phase 3 — Information Gathering & Source Research

Before building theories, systematically gather raw material. The quality of a theory is only as good as the evidence beneath it.

### 3a. Search Strategy

**Start broad, then narrow.** Use layered searches:

1. **Establish the baseline** — What is the official narrative?
   - Search: `"[event name]" official statement OR press release OR report`
   - Look for: government statements, official investigations, mainstream news summaries

2. **Find the cracks** — Where does the official story face criticism?
   - Search: `"[event name]" inconsistencies OR anomalies OR contradictions OR questions`
   - Search: `"[event name]" investigation OR inquiry OR whistleblower`

3. **Follow the money** — Who profited?
   - Search: `"[event name]" financial OR contract OR stock OR beneficiary OR profit`
   - Search: `[key actors] net worth OR funding OR donations OR lobbying`

4. **Find alternative analyses** — What do independent researchers say?
   - Search: `"[event name]" alternative explanation OR independent analysis OR criticism`
   - Search: `"[event name]" site:substack.com OR site:independentresearcher.com`

5. **Historical parallels** — Has something like this happened before?
   - Search: `[pattern type] historical examples OR precedent OR similar event`

### 3b. Source Tiers & Trust Levels

Evaluate every source before using it. Assign a trust tier:

| Tier | Source Type | Trust Level | Notes |
|------|------------|-------------|-------|
| 1 | Primary documents (court filings, leaked docs, official reports, FOIA releases) | High | Still check for authenticity |
| 2 | Academic papers, peer-reviewed research | High | Check funding sources |
| 3 | Established investigative journalism (e.g. ICIJ, ProPublica, Der Spiegel) | Medium-High | Still has editorial bias |
| 4 | Mainstream news outlets | Medium | Cross-reference; known to amplify official narratives |
| 5 | Independent journalists, substack, blogs | Medium-Low | Depends heavily on sourcing quality |
| 6 | Anonymous sources, social media posts, forums | Low | Never use alone; require corroboration |
| 7 | AI-generated content or unsourced claims | Very Low | Require independent verification |

**Key rule:** A claim is only as strong as its weakest supporting source. Always trace claims back to their primary source.

### 3c. Source Diversity — Avoiding the Filter Bubble

Mainstream and alternative media can both be captured or biased. Deliberately seek sources from **opposing viewpoints**:

- Read the official account AND its sharpest critics
- Seek sources from **different countries** — foreign press often covers what domestic press won't
- Search in multiple languages if the event is international
- Look for **pre-event** reporting (before narratives solidified) vs. post-event coverage
- Note: what is NOT being reported can be as informative as what is

### 3d. Web Search Best Practices for Agents

When using web search tools during investigation:

```
DO:
✓ Use specific named entities: people, places, organizations, dates
✓ Search for primary documents: "[event] report filetype:pdf"
✓ Search for financial connections: "[actor A] [actor B] funding OR investment"
✓ Use date ranges to find pre-narrative coverage: "[event] before:[date]"
✓ Search for deleted/archived content: site:web.archive.org "[url]"
✓ Cross-check facts across at least 3 independent sources
✓ Look for the original source when a claim is cited

DON'T:
✗ Accept top search results as truth — they may be SEO-optimized official narratives
✗ Rely on a single source for a key claim
✗ Ignore sources that contradict the emerging theory
✗ Confuse high publication frequency with credibility
✗ Treat Wikipedia as a primary source (it is a secondary source, often edited)
```

### 3e. Key Information to Collect Per Event

For each event under investigation, build a fact file:

```
FACT FILE: [Event Name]
────────────────────────────────────────────
Date & Location:
Key actors named in official narrative:
Official explanation summary:
Primary sources reviewed: [list with URLs]
Contradicting sources reviewed: [list with URLs]
Key claims that lack primary sourcing:
Financial flows identified:
Key figures' backgrounds & connections:
Timeline anomalies:
Physical/forensic evidence available:
Evidence that is missing or was destroyed:
Witnesses: names, statements, credibility notes
```

### 3f. Detecting Source Manipulation

Watch for signs that information may be managed or planted:

- **Simultaneous identical framing** across many outlets (suggests coordinated messaging)
- **Suspicious timing** of leaks or document releases
- **Ad hominem attacks** on researchers rather than refutation of their findings
- **Rapid consensus formation** without adequate investigation time
- **Memory-holed content**: stories that disappear from archives or search results
- **Appeal to authority without evidence**: "experts agree" without naming experts or evidence

---

## Phase 4 — Cui Bono Analysis

Ask: **Who benefits from the outcome?**

For each potential actor, assess:

| Actor | Benefit Type | Benefit Description | Plausibility |
|-------|-------------|---------------------|--------------|
| Party A | Financial / Power / Strategic | … | High/Med/Low |
| Party B | … | … | … |

**Benefit types to consider:**
- Financial gain (follow the money)
- Political power or popularity
- Strategic advantage (benefit may materialize later)
- Elimination of a rival or threat
- Justification for future action (pretext)

**Important:** Cui Bono gives a *starting point*, never direct proof. Multiple actors can benefit simultaneously ("killing multiple birds with one stone").

---

## Phase 5 — Means, Motive, Opportunity Matrix

Build a suspect matrix:

| Suspect | Motive ✓/✗ | Means ✓/✗ | Opportunity ✓/✗ | Score |
|---------|-----------|----------|----------------|-------|
| Actor A | ✓ | ✓ | ✓ | 3/3 |
| Actor B | ✓ | ✗ | ✓ | 2/3 |
| Actor C | ✗ | ✓ | ✗ | 1/3 |

Rank suspects by score. Focus theory development on the highest-scoring actors.

---

## Phase 6 — Reasoning Modes

Use the appropriate reasoning mode for the available evidence:

### Deductive (top-down)
*General rule → specific conclusion*
> "Controlled demolitions always produce free-fall collapses. Building X collapsed in free-fall. Therefore Building X may have been a controlled demolition."

⚠️ A deductively valid argument can still be wrong if the general premise is false.

### Inductive (bottom-up)
*Specific observations → general pattern*
> "Past color revolutions were organized by intelligence services. This event resembles a color revolution. Therefore intelligence service involvement is plausible."

⚠️ Inductive conclusions can always be overturned by exceptions.

### Abductive (best explanation)
*Choose the most plausible explanation from competing hypotheses.*
> Preferred when empirical evidence is scarce. Select the theory that explains the most facts with the fewest unexplained residuals.

### Duck Test (intuitive induction)
> "If it looks like a duck, swims like a duck, and quacks like a duck — it probably is a duck."
Apply when multiple surface characteristics match a known pattern.

---

## Phase 7 — Cognitive Bias Check

Before finalizing a theory, screen for these biases:

| Bias | Description | Mitigation |
|------|------------|------------|
| Apophenia | Seeing patterns that aren't there | Require multiple independent data points |
| Confirmation bias | Favoring evidence that fits the theory | Actively seek disconfirming evidence |
| Anchoring bias | Over-relying on first information | Revisit initial assumptions regularly |
| Availability heuristic | Overweighting easily accessible info | Diversify sources |
| Dunning-Kruger | Overconfidence in limited knowledge | Identify knowledge gaps explicitly |
| Authority bias | Trusting status over argument | Evaluate arguments on merit |
| Motivated reasoning | Believing what is comforting | Ask: "What would falsify this?" |

---

## Phase 8 — Fallacy Detection

Identify these common fallacies in both the official narrative and in the theory being built:

- **Ad Hominem** — Attacking the person, not the argument
- **Straw Man** — Attacking a distorted version of the argument
- **False Dilemma** — Limiting options artificially ("either/or" framing)
- **Hasty Generalization** — Drawing broad conclusions from too few cases
- **False Causation** — Assuming correlation implies causation
- **Circular Reasoning** — Restating the conclusion as evidence
- **Misrepresentation** — Putting words in another party's mouth

When a fallacy is detected, flag it and restate the argument without the fallacy, or acknowledge the argument collapses.

---

## Phase 9 — Theory Construction

Build the hypothesis using this structured format:

```
HYPOTHESIS STATEMENT
─────────────────────────────────────────────
Event: [What happened]
Official narrative: [Summary of official explanation]
Red flags identified: [List from Phase 2]
Primary suspect(s): [From Phase 4, highest MMO score]
Proposed motive(s): [From Phase 3]
Proposed mechanism: [How the act was carried out]
Supporting evidence: [Facts that support the hypothesis]
Predicted consequences: [What else should be true IF this hypothesis is correct]
Falsification criteria: [What evidence would DISPROVE the hypothesis]
Confidence level: [Low / Medium / High] + rationale
```

---

## Phase 10 — Ockham's Razor & Theory Selection

When multiple competing hypotheses exist:

1. **Prefer the hypothesis with fewest unsupported assumptions** (Ockham's Razor / Law of Parsimony)
2. But note: sophisticated actors may deliberately embed complexity to obscure conspiracies — don't blindly discard complex theories
3. Rank theories: Most parsimonious → Most elaborate
4. Start verification with the simplest; escalate only if it fails

---

## Phase 11 — Verification Checklist (Schijf van Vijf)

Before presenting a theory as credible, apply these five tests:

- [ ] **Falsification** — Is the theory falsifiable? What would disprove it?
- [ ] **Ockham's Razor** — Is a simpler explanation equally valid?
- [ ] **Cross-referencing** — Does the theory hold across multiple independent sources?
- [ ] **Empirical evidence** — Is there observable, concrete evidence (not only inference)?
- [ ] **Reproducibility** — Can the reasoning be independently replicated from the same facts?

---

## Scientific Method Workflow (Condensed)

```
1. NOTICE     → Anomaly or inadequacy in official explanation
2. EXPLORE    → Identify candidate actors / known conspiracy patterns
3. DOCUMENT   → Gather all relevant facts
4. HYPOTHESIZE → Connect actors, motives, and facts into a coherent theory
5. PREDICT    → Derive testable consequences of the hypothesis
6. VALIDATE   → Check whether predicted consequences hold; iterate
7. AUDIT      → Peer-review for bias and fallacy; refine
```

---

## Output Format for Agents

When delivering analysis, structure output as:

```markdown
## Event Analysis: [Event Name]

### Red Flags
- [Flag 1]
- [Flag 2]

### Cui Bono — Beneficiaries
| Actor | Benefit | Plausibility |
|-------|---------|-------------|
| …     | …       | …           |

### MMO Suspect Matrix
| Suspect | Motive | Means | Opportunity | Score |
|---------|--------|-------|-------------|-------|

### Hypothesis
[Structured hypothesis from Phase 8]

### Bias & Fallacy Check
[Any detected biases or fallacies + mitigations]

### Confidence Assessment
[Low/Medium/High + reasoning]

### What Would Change This Assessment
[Falsification criteria]
```

---

## Quick Reference — Critical Thinking Questions

| Dimension | Questions |
|-----------|-----------|
| **Who** | Who benefits? Who is harmed? Who had means, motive, opportunity? |
| **What** | What are the strengths/weaknesses of the official narrative? What alternative explanations exist? |
| **Where** | Where are there real-world analogues? Where can more information be found? |
| **When** | When did this occur? When does a similar pattern appear historically? |
| **Why** | Why is this explanation offered? Why might it be incomplete? |
| **How** | How could the act have been executed? How can the theory be tested? |