'''
Batching is static so we need to step-by-step make one jsonl for each task,
submitting and incorporating the results in between.

See https://platform.openai.com/docs/guides/batch

In general, batch JSON entries look like this:

    {"custom_id": "request-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo-0125", "messages": [{"role": "system", "content": "You are a helpful assistant."},{"role": "user", "content": "Hello world!"}],"max_tokens": 1000}}

Since we use the responses API however, the url field has "/v1/responses" and the body has the general format:

    {
      "id": 123,
      "name": "Example Item",
      "description": "This is an example item.",
      "price": 19.99,
      "available": true,
      "tags": ["electronics", "gadget"],
      "details": {
        "manufacturer": "Acme Corp",
        "weight_kg": 0.5
      }
    }
'''

import json
import os
import re
from conllu import parse_incr

from .pipeline import BASE_SCHEMA, TASKS

def prepare_task1_responses_batch_jsonl(
    input_conllu_path: str,
    output_jsonl_path: str,
    model: str = "gpt-5-mini-2025-08-07",
    max_output_tokens: int = 1024,
    batch_prefix: str | None = None,
    extra_body_fields: dict | None = None
) -> int:
    """
    Read a CoNLL-U file and write a JSONL file where each line is a single
    POST /v1/responses request ready for the OpenAI Batch API (Task 1 only).
    
    Each output line has keys:
      - custom_id  (unique per sentence; useful to map results later)
      - method: "POST"
      - url: "/v1/responses"
      - body: { model, instructions, input, ... }
    
    Assumes `BASE_SCHEMA` and `TASKS` are available in the module scope and that
    TASKS[0] is Task 1 (ID, FORM, LEMMA, UPOS).
    
    Returns number_of_requests_written.
    """
    if batch_prefix is None:
        batch_prefix = os.path.splitext(os.path.basename(input_conllu_path))[0]

    entries = []
    sentence_counter = 0

    with open(input_conllu_path, "r", encoding="utf-8") as fh:
        for tokenlist in parse_incr(fh):
            # Prefer # text = ... metadata, fallback to reconstructing from forms
            sent_text = None
            if getattr(tokenlist, "metadata", None):
                sent_text = tokenlist.metadata.get("text")
            if not sent_text:
                forms = [tok.get("form") for tok in tokenlist if tok.get("form")]
                sent_text = " ".join(forms).strip()
                if not sent_text:
                    # skip empty sentence
                    continue

            sentence_counter += 1

            # words split (you asked earlier to split at punctuation)
            input_words = re.findall(r'\w+|[^\w\s]', sent_text, re.UNICODE)

            base_prompt = (
                f"We will perform dependency parsing on this Swedish sentence:\n"
                f"{sent_text}\n\n"
                f"Words: {input_words}\n\n"
                f"{BASE_SCHEMA}\n"
            )

            matsuda_instructions = f"{BASE_SCHEMA}\nNow perform:\n{TASKS[0]}"

            custom_id = f"{batch_prefix}_s{sentence_counter}_t1"

            body = {
                "model": model,
                "instructions": matsuda_instructions,
                "input": base_prompt,
                "max_output_tokens": max_output_tokens,
                # small metadata to make downstream mapping easier
                "metadata": {"sentence_index": sentence_counter, "batch_prefix": batch_prefix}
            }

            if extra_body_fields:
                # allow overriding or extending body (e.g. temperature, stop, etc.)
                body.update(extra_body_fields)

            entry = {
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/responses",
                "body": body
            }

            entries.append(entry)

    # write JSONL
    with open(output_jsonl_path, "w", encoding="utf-8") as out_f:
        for e in entries:
            out_f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"[prepare_task1_responses_batch_jsonl] wrote {len(entries)} requests -> {output_jsonl_path}")
    return len(entries)

def prepare_task2_responses_batch_jsonl(
    task1_results_jsonl: str,
    output_jsonl_path: str,
    model: str = "gpt-5-mini-2025-08-07",
    max_output_tokens: int = 4096,
):
    """
    Read Task 1 batch results (JSONL from /v1/responses) and prepare a new JSONL
    for Task 2 (adding FEATS). Each request body.input is set to the Task 1 output.
    """
    entries = []
    with open(task1_results_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            result = json.loads(line)
            custom_id = result.get("custom_id")
            if not custom_id:
                continue

            # Example: "mytreebank_s3_t1" → prefix="mytreebank", sentence=3
            if not custom_id.endswith("_t1"):
                continue
            prefix = custom_id.rsplit("_", 1)[0]  # remove _t1
            sentence_idx = prefix.split("_s")[-1]

            # Task 1 output text from Responses API
            try:
                task1_output = result["response"]["output"][0]["content"][0]["text"]
            except Exception:
                raise ValueError(f"Could not extract output text from result: {custom_id}")

            # Build Task 2 request
            task2_custom_id = f"{prefix}_t2"
            matsuda_instructions = f"{BASE_SCHEMA}\nNow perform:\n{TASKS[1]}"

            body = {
                "model": model,
                "instructions": matsuda_instructions,
                "input": task1_output,
                "max_output_tokens": max_output_tokens,
                "metadata": {"sentence_index": int(sentence_idx), "batch_prefix": prefix},
            }

            entry = {
                "custom_id": task2_custom_id,
                "method": "POST",
                "url": "/v1/responses",
                "body": body,
            }
            entries.append(entry)

    with open(output_jsonl_path, "w", encoding="utf-8") as out_f:
        for e in entries:
            out_f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"[prepare_task2_responses_batch_jsonl] wrote {len(entries)} requests -> {output_jsonl_path}")
    return len(entries)