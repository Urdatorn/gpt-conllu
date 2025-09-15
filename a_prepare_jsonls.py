#!/usr/bin/env python3
"""
Convert CoNLL-U file to JSONL format for OpenAI API training/evaluation.
Each sentence becomes a prompt-response pair where:
- Prompt: The raw text
- Response: Tab-separated CoNLL-U formatted dependency structure
"""

import json
import re
from typing import List, Dict, Tuple


def parse_conllu_file(filepath: str) -> List[Tuple[str, str]]:
    """
    Parse a CoNLL-U file and extract text-annotation pairs.
    
    Returns:
        List of (text, conllu_tsv) tuples
    """
    pairs = []
    current_text = None
    current_annotations = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                # If we have accumulated data, save it
                if current_text and current_annotations:
                    conllu_tsv = '\n'.join(current_annotations)
                    pairs.append((current_text, conllu_tsv))
                    current_text = None
                    current_annotations = []
                continue
            
            # Extract text from comment lines
            if line.startswith('# text = '):
                current_text = line[9:]  # Remove '# text = ' prefix
            
            # Skip other comment lines
            elif line.startswith('#'):
                continue
            
            # Process token lines (tab-separated)
            else:
                current_annotations.append(line)
    
    # Handle the last sentence if file doesn't end with empty line
    if current_text and current_annotations:
        conllu_tsv = '\n'.join(current_annotations)
        pairs.append((current_text, conllu_tsv))
    
    return pairs


def create_openai_jsonl(pairs: List[Tuple[str, str]], output_file: str):
    """
    Create JSONL file in OpenAI format from text-annotation pairs.
    
    Args:
        pairs: List of (text, conllu_tsv) tuples
        output_file: Path to output JSONL file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for text, conllu_tsv in pairs:
            # Create the training example in OpenAI format
            example = {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Parse the following Swedish text into CoNLL-U format:\n\n{text}"
                    },
                    {
                        "role": "assistant", 
                        "content": conllu_tsv
                    }
                ]
            }
            
            # Write as single line JSON
            f.write(json.dumps(example, ensure_ascii=False) + '\n')


def create_eval_jsonl(pairs: List[Tuple[str, str]], output_file: str):
    """
    Create JSONL file in evaluation format (prompt-response pairs).
    
    Args:
        pairs: List of (text, conllu_tsv) tuples  
        output_file: Path to output JSONL file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, (text, conllu_tsv) in enumerate(pairs):
            # Create the evaluation example
            example = {
                "id": f"conllu_eval_{i:04d}",
                "prompt": f"Parse the following Swedish text into CoNLL-U format:\n\n{text}",
                "expected_response": conllu_tsv,
                "metadata": {
                    "text": text,
                    "task": "conllu_parsing",
                    "language": "sv"
                }
            }
            
            # Write as single line JSON
            f.write(json.dumps(example, ensure_ascii=False) + '\n')


def main():
    input_file = 'sv_pud-ud-test.conllu'
    
    print(f"Parsing {input_file}...")
    pairs = parse_conllu_file(input_file)
    print(f"Found {len(pairs)} text-annotation pairs")
    
    # Show first example
    if pairs:
        text, conllu = pairs[0]
        print(f"\nFirst example:")
        print(f"Text: {text}")
        print(f"CoNLL-U (first 3 lines):")
        print('\n'.join(conllu.split('\n')[:3]))
    
    # Create OpenAI training format
    training_output = 'sv_conllu_training.jsonl'
    print(f"\nCreating OpenAI training format: {training_output}")
    create_openai_jsonl(pairs, training_output)
    
    # Create evaluation format
    eval_output = 'sv_conllu_eval.jsonl'
    print(f"Creating evaluation format: {eval_output}")
    create_eval_jsonl(pairs, eval_output)
    
    print(f"\nCompleted! Generated:")
    print(f"- {training_output} (OpenAI training format)")
    print(f"- {eval_output} (Evaluation format)")


if __name__ == "__main__":
    main()