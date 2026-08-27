# Context Window — LLM Fundamentals

Ab next important concept: **Context Window**. Ye tokens ka hi direct extension hai, aur baad mein RAG + Agents mein ye bahut zyada important ho jaayega — isliye is concept ko solid samajhna zaroori hai.

## 1. Context Window Kya Hai?

**Context window = maximum amount of information (tokens mein measure hoti hai) jo ek model ek request ke liye context ke roop mein consider kar sakta hai.**

Simple mental model:

```
                 CONTEXT WINDOW
┌─────────────────────────────────────────┐
│ System instructions                     │
│                                         │
│ Conversation history                    │
│                                         │
│ Current user request                    │
│                                         │
│ Retrieved documents                     │
│                                         │
│ Tool definitions                        │
│                                         │
│ Tool results                            │
│                                         │
│                  ↓                      │
│               LLM MODEL                 │
└─────────────────────────────────────────┘
```

Jo bhi cheez tu model ke context mein daalta hai — wo sab tokens consume karti hai. System instructions ho, purani conversation ho, ya retrieved documents — sab context window ke andar hi ginte hain.

## 2. Context Window ≠ Memory

**Ye ek bahut important interview concept hai.** Yahan pe log confuse ho jaate hain, isliye dhyan se samajh.

Maan le tu LLM ko batata hai:

```
User:
My name is Tridibesh.
```

Phir baad mein:

```
User:
What's my name?
```

Model correctly answer de sakta hai — **agar** relevant information usse jo context mila hai usme available ho. Lekin iska matlab ye bilkul nahi hai ki model ke paas tera permanent memory hai.

Farak samajh:

```
Context
   ↓
Temporary information available to model
```

versus:

```
Memory
   ↓
Information stored/retrieved by an external system
```

Baad mein jab hum agents padhenge, tab hum actual memory architectures deal karenge — jahan information sach mein persist hoti hai, sirf ek request ke duration tak nahi.

## 3. Context Ke Andar Kya Hota Hai?

Ek API request ke liye, context mein user ke latest message se kaafi zyada cheezein ho sakti hain.

Example:

```
System instructions
+
Conversation history
+
Current user message
+
Tool definitions
+
Tool results
+
Retrieved RAG documents
```

Toh:

```
Total Context
=
System
+
History
+
User
+
Tools
+
Retrieved Data
+
Other relevant context
```

Ye sab mil ke token usage mein contribute karte hain — sirf "user ne kya bola" utna hi nahi.

## 4. Example

Maan le teri application mein:

```
System instructions: 1,000 tokens

Conversation:         4,000 tokens

User request:           500 tokens

Tool definitions:       800 tokens

Retrieved documents:  5,000 tokens
```

Toh roughly:

```
Total input context
=
1000
+ 4000
+ 500
+ 800
+ 5000

= 11,300 tokens
```

Model sirf yeh nahi process kar raha:

```
"User request"
```

Wo poora supplied context process kar raha hai — jo tu bhej raha hai wo sab.

## 5. Context Window Ki Limit

Har model ki ek finite context capacity hoti hai.

Ek hypothetical model soch, jiska:

```
Context window = 32,000 tokens
```

Aur tu bhej raha hai:

```
Input context = 30,000
```

Ab tere paas output ke liye unlimited room nahi bacha. Agar tujhe chahiye:

```
Output = 5,000 tokens
```

to tu model ke context/output constraints mein fas sakta hai.

Conceptually:

```
┌──────────────────────────────┐
│       Context Capacity       │
│                              │
│ Input context                │
│ ████████████████████████     │
│                              │
│ Output                       │
│ █████                       │
└──────────────────────────────┘
```

**Note:** Exact limits aur accounting model/API pe depend karte hain, isliye koi universal formula yaad mat kar. Hamesha specific model ki current documentation check kar.

## 6. Context Windows Kyun Matter Karte Hain?

AI backend engineering ke liye, iske chaar major reasons hain.

### ① Cost

Zyada input tokens generally zyada input-token usage matlab rakhte hain.

```
Context ↑
   ↓
Input tokens ↑
   ↓
Cost ↑
```

### ② Latency

Bade requests processing time badha sakte hain.

```
Context ↑
   ↓
More processing
   ↓
Potential latency ↑
```

Isse strict linear relationship mat samajh — model architecture aur provider implementation bhi yahan matter karte hain.

### ③ Context Limits

Eventually tu model ki acceptable capacity exceed kar sakta hai.

```
Context
   ↓
████████████████████████
   ↓
LIMIT
```

Teri application ko isse handle karna hi padega.

### ④ Quality

Ye thoda subtle point hai.

**Zyada context automatically better answers ka matlab nahi hai.**

Maan le tu model ko deta hai:

```
100 relevant tokens
+
50,000 irrelevant tokens
```

versus:

```
2,000 highly relevant tokens
```

Doosra kaafi better ho sakta hai. Yehi ek wajah hai ki RAG mein retrieval quality itna matter karta hai — junk context daalne se answer better nahi, kharab hota hai.

## 7. Lambi Conversations

Ek chatbot conversation socho:

```
Turn 1
100 tokens

Turn 2
300 tokens

Turn 3
500 tokens

Turn 4
800 tokens

...

Turn 50
???
```

Agar teri application blindly poori conversation har baar bhej rahi hai:

```
Request 1 → small context
Request 2 → larger context
Request 3 → larger context
...
Request 50 → huge context
```

Tujhe milega:

```
Cost ↑
Latency ↑
Context usage ↑
```

**Isliye production systems ko context management chahiye hi hoti hai** — ye optional nahi hai, ek certain scale ke baad mandatory ban jaata hai.

## 8. Context Management — Strategies

Iski kai strategies hain.

### Strategy 1 — Truncation

Purane messages hata de.

```
Oldest
  ↓
DELETE
  ↓
Recent messages
```

Simple hai, lekin potentially important information lose kar sakta hai.

### Strategy 2 — Summarization

Instead of retain karne ke:

```
10,000 tokens of conversation
```

tu bana sakta hai:

```
1,000-token summary
```

Phir use kar:

```
Summary
+
Recent messages
```

Isse context size kam ho jaata hai. Lekin summarization khud bhi information lose kar sakta hai, isliye isse magic mat samajh — kuch nuance kho sakta hai.

### Strategy 3 — Retrieval

Information ko externally store kar, aur sirf relevant cheez retrieve kar.

```
Conversation / Documents
          ↓
       Database
          ↓
       Retrieval
          ↓
Relevant information
          ↓
          LLM
```

Ye RAG ke peeche ka core idea hai.

### Strategy 4 — Selective Context

Sab kuch mat bhej.

Example:

```
50 previous messages
        ↓
Find relevant messages
        ↓
Send only 5
```

Ye especially agents aur large applications ke liye useful hai.

## 9. RAG Mein Context Window

Yahan pe aaj ka concept extremely important ban jaata hai.

**Bad RAG:**

```
User query
    ↓
Retrieve 100 documents
    ↓
Send everything to LLM
```

Potential result:

```
Huge context
↓
Higher cost
↓
More latency
↓
Potential context overflow
↓
More irrelevant information
```

**Better approach:**

```
User query
    ↓
Retriever
    ↓
Top relevant chunks
    ↓
Reranker
    ↓
Best chunks
    ↓
LLM
```

Yehi exact cheez hum baad mein actually build karenge.

## 10. Tool Calling Mein Context Window

Socho tere agent ke paas 20 tools hain.

Har tool ke paas:

```
name
description
parameters
schema
```

Ye tool definitions khud context lete hain.

Phir model generate karta hai:

```
Tool call
```

Phir tera backend usse execute karta hai. Phir tu wapas bhejta hai:

```
Tool result
```

model ko.

Toh ek agent repeatedly apna context badha sakta hai:

```
User
 ↓
LLM
 ↓
Tool call
 ↓
Tool result
 ↓
LLM
 ↓
Tool call
 ↓
Tool result
 ↓
LLM
```

Har step information add kar sakta hai. Yehi ek wajah hai ki **agent context management ek serious engineering problem ban jaata hai** — jitne zyada tool calls, utna zyada context accumulate hota jaata hai.

## 11. Context vs Output

Ek useful mental model:

```
             MODEL REQUEST
                  │
        ┌─────────┴─────────┐
        ↓                   ↓
     Input                Output
     Context              Generated
        │                   │
        ↓                   ↓
  Existing tokens       New tokens
```

Model existing context receive karta hai aur naye tokens generate karta hai.

Blindly ye mat soch:

```
context window = only input
```

Exact accounting model/API pe depend karta hai, lekin important engineering idea ye hai: **teri request ko utni capacity chahiye jo tu context de raha hai + jo output tu expect kar raha hai — dono ke liye.**

## 12. Context Window vs Knowledge

Ek aur common misconception:

> "Agar model ka context window huge hai, to usse sab pata hai."

**Nahi.**

Context window is about — tu ek request mein model ko kitni information provide kar sakta hai. Ye same cheez nahi hai:

```
training data
permanent memory
database
knowledge base
```

Farak samajh:

```
Training
   ↓
What the model learned

Context
   ↓
What you provide right now

External Memory / DB
   ↓
What your application stores
```

Teeno alag-alag cheezein hain — inko mix mat kar.

## 13. Bada Context Hamesha Better Kyun Nahi Hota

Socho:

```
Context A
2,000 relevant tokens
```

versus:

```
Context B
100,000 tokens
```

jahan sirf 2,000 relevant hain.

Tu shayad assume karega:

> "100K better hai kyunki zyada information hai."

**Galat.**

Tujhe chahiye:

```
High relevance
+
Enough context
+
Low unnecessary tokens
```

Yehi wajah hai ki good AI systems context **quality** ki fikar karte hain, sirf context **size** ki nahi.

## 14. Backend Engineering Mental Model

Jab bhi ek AI system design kar raha ho, khud se ye poochh:

```
How much context are we sending?
        ↓
Is it necessary?
        ↓
Can we retrieve only relevant information?
        ↓
Can we summarize old information?
        ↓
Can we remove redundant tool results?
        ↓
What's the token cost?
        ↓
What's the latency?
```

Yehi mindset chahiye tujhe har AI system banate waqt.

## 15. Interview-Level Questions

Tujhe ye sab confidently answer kar paana chahiye:

**Q1. Context window kya hai?**
A. Tokenized information ki wo amount jo ek model ek request ke context ke roop mein process kar sakta hai, specific model/API ki limits ke subject.

**Q2. Kya context window aur memory same hain?**
A. Nahi. Context wo information hai jo ek request ke liye model ko supply ki jaati hai; application memory typically externally store hoti hai aur zarurat padne pe retrieve ki jaati hai.

**Q3. Lambi conversation expensive kyun ban jaati hai?**
A. Kyunki subsequent requests mein zyada conversation history maintain karne se input context/tokens ki amount badhti jaati hai jo process hoti hai.

**Q4. Kya bada context hamesha better results deta hai?**
A. Nahi. Irrelevant ya redundant context cost aur latency badha sakta hai aur answer quality kam kar sakta hai. Relevant context sirf zyada context hone se zyada important hai.

**Q5. Hum context size control kaise kar sakte hain?**
A. Ye mention karna chahiye:

```
truncation
summarization
retrieval
selective context
limiting tool results
chunking
removing redundant information
```

## 🔥 Wo Mental Model Jo Yaad Rakhna Hai

```
                USER REQUEST
                     │
                     ▼
          ┌─────────────────────┐
          │   CONTEXT WINDOW    │
          │                     │
          │ System instructions │
          │ Conversation        │
          │ User request        │
          │ Tool definitions    │
          │ Tool results        │
          │ Retrieved context   │
          │                     │
          └──────────┬──────────┘
                     │
                     ▼
                    LLM
                     │
                     ▼
               Output tokens
```

Aur ye raha AI-engineering ka principle jo hamesha yaad rakhna:

> **Don't maximize context. Maximize useful context.**
>
> Context ko maximize mat kar — useful context ko maximize kar.