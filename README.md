# GPT CoNLL-U
Prompt engineering GPTs for UD-style parsing of pre-modern Swedish.
Part of the group research project ``Diachronic Treebanks`` of DigPhil.

Task division inspired by [Matsuda 2025](media/Matsuda-2025-LLM-dependency-parsing.pdf), but using one prompt per task instead of chain-of-thought. 
To minimize risk of hallucination, the gpt uses placeholders for tabs, 
and the actual ten tab `.conllu` is made programmatically once all tasks are done. There are five tasks, with the first task being longer (like Matsuda) and the following each adding one field. To make life easier for the model, we exclude `XPOS` and `MISC` and automatically map them to `_` afterwards.

With the current task prompt, the cheapest model `gpt-5-nano`
is not able to come up with `FEAT`, but `gpt-5-mini` is (for reproducibility we specifically use the snapshot `gpt-5-mini-2025-08-07`).

For example, input `"Thetta är inte begynnilsen aff Jesu Christi gudz sons euangelio."` (the first sentence of the 1526 gospel of Mark with an added negation) results in the following tree, which at least at first glance looks acceptable for our purposes:

![Conllu viewer example](media/conllu-viewer-example.png)

See [the main notebook](main.ipynb) for instructions and examples of running the pipeline on your texts of choice.