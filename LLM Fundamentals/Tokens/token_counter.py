"""
token_counter.py
Production-grade Token Counting, Cost Estimation & BPE (Byte Pair Encoding) Simulator.
Supports:
1. Exact OpenAI BPE Tokenization using tiktoken (cl100k_base for GPT-4o / GPT-4 / text-embedding-3)
2. Heuristic fallback when tiktoken is unavailable
3. Chat Completion Message Format Overhead Calculation (exact OpenAI per-message framing tokens)
4. Dynamic Token Cost Calculation across standard models
"""

import math
from typing import List, Dict, Any, Optional

try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False


# Standard Model Pricing Table (USD per 1 Million Tokens)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"input": 5.00, "output": 15.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
}


class TokenCounter:
    def __init__(self, default_encoding: str = "cl100k_base"):
        self.default_encoding = default_encoding
        if HAS_TIKTOKEN:
            try:
                self.encoder = tiktoken.get_encoding(default_encoding)
            except Exception:
                self.encoder = None
        else:
            self.encoder = None

    def count_string_tokens(self, text: str) -> int:
        """Counts exact tokens for a plain string using BPE tokenizer or heuristic fallback."""
        if not text:
            return 0
        if self.encoder:
            return len(self.encoder.encode(text))
        # Heuristic fallback: ~4 characters per token in English, ~1.5 per token in code/JSON
        return max(1, math.ceil(len(text) / 4.0))

    def count_chat_tokens(self, messages: List[Dict[str, str]], model: str = "gpt-4o") -> int:
        """
        Calculates exact tokens consumed by OpenAI Chat Completions API format.
        OpenAI applies specific structural framing overhead:
        - Every message adds 3 tokens: <|start|>{role/name}\n{content}<|end|>
        - Every reply is primed with 3 assistant tokens: <|start|>assistant<|message|>
        """
        if self.encoder is None:
            # Fallback estimation
            total = sum(self.count_string_tokens(m.get("content", "")) + 4 for m in messages)
            return total + 3

        num_tokens = 0
        for message in messages:
            num_tokens += 3  # <|im_start|>{role} ... <|im_end|>
            for key, value in message.items():
                num_tokens += len(self.encoder.encode(value))
                if key == "name":
                    num_tokens += 1  # Additional name framing

        num_tokens += 3  # Priming tokens for assistant response
        return num_tokens

    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> Optional[float]:
        """Calculates total cost in USD for a given prompt and completion usage."""
        pricing = MODEL_PRICING.get(model.lower())
        if not pricing:
            return None
        input_cost = (prompt_tokens / 1_000_000.0) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000.0) * pricing["output"]
        return round(input_cost + output_cost, 6)


# =====================================================================
# Verification & Interactive Demonstration
# =====================================================================
if __name__ == "__main__":
    counter = TokenCounter()

    sample_text = (
        "Large Language Models process text using Byte Pair Encoding (BPE). "
        "A word can be split into multiple subword tokens: 'unbelievable' -> ['un', 'believ', 'able']."
    )

    print("=========================================================")
    print(f"TOKEN COUNTING & COST ESTIMATOR (Using Tiktoken: {HAS_TIKTOKEN})")
    print("=========================================================")

    token_count = counter.count_string_tokens(sample_text)
    print(f"Text String: '{sample_text}'")
    print(f"Character Count : {len(sample_text)} characters")
    print(f"Exact Token Count: {token_count} tokens")
    print(f"Ratio           : {len(sample_text) / token_count:.2f} chars/token\n")

    # Chat completion payload simulation
    chat_payload = [
        {"role": "system", "content": "You are a senior backend AI infrastructure engineer."},
        {"role": "user", "content": "Explain how BPE tokenization handles whitespace and code syntax."},
        {"role": "assistant", "content": "BPE treats spaces as distinct character bytes (often displayed as 'Ġ' or ' ')."}
    ]

    chat_tokens = counter.count_chat_tokens(chat_payload, model="gpt-4o")
    print("--- Chat History Framing Token Breakdown ---")
    print(f"Total Chat Payload Tokens (including formatting overhead): {chat_tokens}")

    # Cost calculations
    est_completion_tokens = 500
    cost_gpt4o = counter.estimate_cost("gpt-4o", prompt_tokens=chat_tokens, completion_tokens=est_completion_tokens)
    cost_mini = counter.estimate_cost("gpt-4o-mini", prompt_tokens=chat_tokens, completion_tokens=est_completion_tokens)

    print("\n--- Estimated Cost Comparison (assuming 500 completion tokens) ---")
    print(f"GPT-4o      : ${cost_gpt4o:.6f} USD")
    print(f"GPT-4o-mini : ${cost_mini:.6f} USD (Savings: {((cost_gpt4o - cost_mini)/cost_gpt4o)*100:.1f}%)")
