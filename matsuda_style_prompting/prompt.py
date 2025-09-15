import re
import textwrap

def make_prompt(input_sentence):
    # Split at words **or** punctuation
    input_words = re.findall(r'\w+|[^\w\s]', input_sentence, re.UNICODE)

    instructions = f"""
    You are a Swedish linguist and specialize in
    Swedish dependency analysis based on Universal
    Dependencies.

    We will now perform dependency parsing on a Swedish
    sentence. After splitting the input sentence into
    words as shown below, execute the following three
    tasks:

    - Task 1
    Create a TSV with three fields: word index from 1
    to {len(input_words)} + word + part of speech.

    - Task 2
    Add a field for the dependent word indexes to
    each row to the output of Task 1. However, for
    the word that is the main predicate of the
    sentence, the dependent word index should be 0.

    - Task 3
    Add a field for the Universal Dependencies
    relation labels to the output of Task 2.

    - Task 4
    Add a field for the head word indexes to the
    output of Task 3. The head word index is the
    index of the word that this word depends on.
    For the main predicate of the sentence, the
    head word index should be 0.

    - Task 5
    Add a field for morphological features to
    the output of Task 4. If there are no features,
    use an underscore (_).

    - Task 6

    **Swedish POS / Morphology rules** (from Swedish UD guidelines):

   - Use **all 17 universal UPOS tags**.  
   - Tag PART only for: the infinitive marker *att*; and the negation particles *inte, icke, ej*.  
   - AUX includes:  
     • the copula *vara* (“be”)  
     • the temporal auxiliary *ha* (“have”) for perfect tenses, combining with supine  
     • the passive auxiliary *bli* (“get”) with past participle for passives  
     • modal / aspectual verbs that take a bare infinitive (e.g. *måste*, *kunde*)  
   - Participles (present & past):  
     • if used adjectivally → tag as ADJ  
     • **exception**: past participles used in **periphrastic passives** with *bli* → tag as VERB  
   - Nouns: mark features Number (Sing, Plur), Definite (Indef, Def), Case (Nom, Gen), Gender.  
   - Adjectives: must agree with nouns (both in attributive and predicate position) in Gender, Number, Definite; also features for Degree (Pos, Comp, Sup); case for adjectives only when heading noun phrases; ordinals use NumType.  
   - Pronouns: personal pronouns inflect for Case (Nom, Acc, Gen). Possessives are tagged as **PRON**, not DET. Determiners (tag DET) are used for articles etc., but not possessives.

    Do not add any extra commentary, 
    just return the 3 TSV tables, separated by blank lines.
    """
    
    instructions = textwrap.dedent(instructions)

    prompt_text = f"Input sentence:\n{input_sentence}\n\nWords:\n"
    for word in input_words:
        prompt_text += f"{word}\n"
    
    return instructions, prompt_text

if __name__ == "__main__":
    input_sentence = "Thetta är begynnilsen aff Jesu Christi gudz sons euangelio."
    instructions, prompt_text = make_prompt(input_sentence)
    print(instructions)
    print(prompt_text)