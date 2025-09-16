from conllu import parse_incr
import json
from openai import OpenAI
import os
import re
from tqdm import tqdm

##############
# --- Aux ---
############## 

def is_valid_conllu(filepath: str) -> bool:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for _ in parse_incr(f):
                pass
        return True
    except Exception:
        return False

##################
# --- API call ---
##################

api_key = os.getenv("OPENAI_API_KEY_TREEBANKS") 
client = OpenAI(api_key=api_key)

def call_api(prompt_text, matsuda_instructions, model):
    response = client.responses.create(
        #model="ft:gpt-4.1-nano-2025-04-14:personal:swe-conllu:CFvbo29L:ckpt-step-200",
        model=model,
        instructions=matsuda_instructions,
        input=prompt_text
    )
    return response.output_text

##############################
# --- Pipeline multiprompt ---
##############################

BASE_SCHEMA = """Each row must have exactly 8 fields in the order:
ID⟶FORM⟶LEMMA⟶UPOS⟶FEATS⟶HEAD⟶DEPREL⟶DEPS
Do not include XPOS or MISC. Use "⟶" (not spaces, not tabs) as the separator.
"""

TASKS = [
    "- Task 1\nAssign ID, FORM, LEMMA, UPOS.",
    "- Task 2\nAdd FEATS. If none, use _. Use the Universal Dependencies morphological features inventory. "
    "Each feature must be an attribute=value pair (e.g. Gender=Com, Number=Sing, Case=Nom). "
    "Multiple features are separated by | and sorted alphabetically by attribute. "
    "Here is an example from Swedish UD:\n"
    "3⟶han⟶han⟶PRON⟶-⟶Case=Nom|Definite=Def|Gender=Com|Number=Sing\n"
    "4⟶elva⟶elva⟶NUM⟶-⟶Case=Nom|NumType=Card\n"
    "5⟶år⟶år⟶NOUN⟶-⟶Case=Nom|Definite=Ind|Gender=Neut|Number=Plur\n"
    "Follow this format exactly.",
    "- Task 3\nAdd HEAD. For main predicate use 0.",
    "- Task 4\nAdd DEPREL.",
    "- Task 5\nAdd DEPS. If none, use _."
]

def pipeline(input, model="gpt-5-mini-2025-08-07"):
    def run_pipeline(input_sentence):
        input_words = re.findall(r'\w+|[^\w\s]', input_sentence, re.UNICODE)

        # initial context for the model
        prompt = (
            f"We will perform dependency parsing on this Swedish sentence:\n"
            f"{input_sentence}\n\n"
            f"Words: {input_words}\n\n"
            f"{BASE_SCHEMA}\n"
        )
        
        output = None
        for i, task in tqdm(enumerate(TASKS, start=1)):
            matsuda_instructions = f"{BASE_SCHEMA}\nNow perform:\n{task}"
            prompt_text = output if output else prompt
            output = call_api(prompt_text, matsuda_instructions, model=model)
            
            if not os.path.exists("output/debug"):
                os.makedirs("output/debug")
            with open(f"output/debug/task{i}.tsv", "w", encoding="utf-8") as f:
                f.write(output)

        return output

    def finalize_conllu(final_output):
        """Convert placeholders to real TSV, add XPOS=_ and MISC=_."""
        lines = []
        for line in final_output.strip().splitlines():
            if not line.strip():
                continue
            fields = line.split("⟶")
            if len(fields) != 8:
                raise ValueError(f"Expected 8 fields, got {len(fields)} in line: {line}")
            # Insert XPOS = "_" at index 4 (5th column)
            fields.insert(4, "_")
            # Add MISC = "_" at the end
            fields.append("_")
            lines.append("\t".join(fields))
        return "\n".join(lines)
    
    result = run_pipeline(input)
    return finalize_conllu(result)
