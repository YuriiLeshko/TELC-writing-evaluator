# TELC B2 Writing Assessment Guidelines (Schriftlicher Ausdruck)

## Overview

This document defines a **structured, rule-based evaluation system** for TELC B2 writing tasks.  
Assessment is based on **three independent criteria**:

1. Task Achievement (Criterion I)
2. Communicative Design (Criterion II)
3. Formal Accuracy (Criterion III)

Each criterion is graded:

| Grade | Points |
|-------|--------|
| A     | 5      |
| B     | 3      |
| C     | 1      |
| D     | 0      |

### Final Score


Final Score = (I + II + III) × 3
Max Score = 45


---

## 1. Pre-checks

### 1.1 Topic Mismatch (Thema verfehlt)

If the text:
- is unrelated to the task
- or barely related

→ Assign:


I = D
II = D
III = D


---

### 1.2 Situation Mismatch (Situierung verfehlt)

If the topic is relevant but the **situation is wrong**:

→ Assign:


I = D
II and III evaluated normally


---

## 2. Criterion I: Task Achievement

### Definition

Evaluates how well the response fulfills the **task requirements**.

---

### Valid Leitpunkt (Key Point)

A key point is considered fulfilled if:

- directly relevant to the task
- appropriate to the situation
- developed beyond one sentence
- sufficiently detailed
- at B2 level

---

### Grades

#### A (5 points)

- 3 key points fulfilled  
  OR  
- 2 key points + 1 relevant own idea

All must be:
- clearly developed
- appropriate
- at B2 level

---

#### B (3 points)

- 2 key points fulfilled  
  OR  
- 1 key point + 1 own idea

---

#### C (1 point)

- Only 1 key point fulfilled

---

#### D (0 points)

- No key points adequately fulfilled

---

## 3. Criterion II: Communicative Design

### Definition

Evaluates:

- structure
- coherence
- cohesion
- style/register
- vocabulary range
- text type (email)

---

### Required Email Elements

Expected for high scores:

- Subject line (Betreff)
- Greeting (Anrede)
- Introduction
- Logical body structure
- Conclusion
- Closing formula

---

### Grades

#### A (5 points)

- clear and convincing communication
- appropriate formal/semi-formal style
- well-structured
- strong logical flow
- varied linking devices
- wide vocabulary range
- varied sentence structures

**Cannot receive A if:**
- missing subject, greeting, or closing
- vocabulary not fully B2-level

---

#### B (3 points)

- generally clear
- appropriate style
- structured
- some linking devices
- adequate vocabulary
- some ability to express complex ideas

**Cannot receive B if:**
- wrong or inconsistent register
- insufficient vocabulary for B2
- ideas listed without logical connection

---

#### C (1 point)

- understandable but simple
- weak structure
- limited linking
- repetitive or list-like
- vocabulary closer to B1
- partially inappropriate style

---

#### D (0 points)

- incoherent or illogical
- almost no linking devices
- inappropriate register
- very limited vocabulary
- A2 level or below

---

## 4. Criterion III: Formal Accuracy

### Definition

Evaluates:

- grammar
- syntax
- word order
- verb forms
- agreement
- spelling
- punctuation
- capitalization

---

### Grades

#### A (5 points)

- strong grammatical control
- no systematic errors
- only minor mistakes
- correct spelling and punctuation
- errors do not affect understanding

---

#### B (3 points)

- generally good grammar
- few systematic errors
- errors do not hinder comprehension
- minor influence of first language

---

#### C (1 point)

- adequate but unstable grammar
- several systematic errors
- mostly understandable
- noticeable mistakes

---

#### D (0 points)

- frequent basic errors
- incorrect sentence structures
- tense confusion
- agreement errors
- spelling often phonetic
- parts difficult to understand

---

## 5. Evaluation Algorithm

Check topic relevance
If failed → D/D/D
Check situation relevance
If failed → I = D
Identify fulfilled key points
Assign Criterion I
Evaluate structure, logic, style
Assign Criterion II
Evaluate grammar and correctness
Assign Criterion III
Convert grades to points
Calculate final score

---

## 6. Output Format (Recommended)

```json
{
  "topic_mismatch": false,
  "situation_mismatch": false,
  "criterion_I": {
    "grade": "B",
    "points": 3
  },
  "criterion_II": {
    "grade": "B",
    "points": 3
  },
  "criterion_III": {
    "grade": "C",
    "points": 1
  },
  "raw_score": 7,
  "final_score": 21,
  "max_score": 45
}
```

## 7. Core Principle
First evaluate content.
Then structure and communication.
Only then grammar.