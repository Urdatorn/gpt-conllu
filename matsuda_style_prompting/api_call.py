from openai import OpenAI
import os
from prompt import make_prompt

api_key = os.getenv("OPENAI_API_KEY_TREEBANKS") 
client = OpenAI(api_key=api_key)

def call_api(prompt_text, matsuda_instructions):
    response = client.responses.create(
        model="gpt-5-nano",
        instructions=matsuda_instructions,
        input=prompt_text
    )
    return response.output_text

if __name__ == "__main__":
    input_sentence = "Thetta är begynnilsen aff Jesu Christi gudz sons euangelio."
    prompt_text, matsuda_instructions = make_prompt(input_sentence)
    print(prompt_text, matsuda_instructions)

    response = call_api(prompt_text, matsuda_instructions)
    print(response)
