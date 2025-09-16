import tiktoken
from .pipeline import BASE_SCHEMA, TASKS

def count_total_tokens_and_cost(conllu_path: str, model: str = "gpt-4o-mini",
                                cost_per_million_input_tokens: float = 0.125,
                                cost_per_million_output_tokens: float = 1.0):
    encoding = tiktoken.encoding_for_model(model)

    # Extract text lines
    texts = []
    with open(conllu_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("# text ="):
                texts.append(line[len("# text ="):].strip())
    num_texts = len(texts)

    # Tokens in text lines
    combined_text = "\n".join(texts)
    text_tokens = len(encoding.encode(combined_text))

    # Tokens in prompts
    base_schema_tokens = len(encoding.encode(BASE_SCHEMA))
    tasks_tokens = sum(len(encoding.encode(task)) for task in TASKS)
    per_text_prompt_tokens = base_schema_tokens + tasks_tokens

    # Total input tokens
    total_input_tokens = text_tokens + per_text_prompt_tokens * num_texts
    input_cost = total_input_tokens / 1_000_000 * cost_per_million_input_tokens

    # Nested function to estimate output cost
    def estimate_output_cost(example_line: str) -> float:
        # Tokens for one example line
        example_tokens = len(encoding.encode(example_line))
        # Multiply by 5 tasks, then by number of text inputs
        total_output_tokens = example_tokens * 5 * num_texts
        # Approximate output cost
        return total_output_tokens / 1_000_000 * cost_per_million_output_tokens

    # Example line (fully completed)
    example_line = "1\tThetta\tthetta\tPRON\t_\tCase=Nom|Gender=Neut|Number=Sing|PronType=Dem\t4\tnsubj\t4:nsubj\t_"
    output_cost = estimate_output_cost(example_line)

    return total_input_tokens, input_cost, output_cost
