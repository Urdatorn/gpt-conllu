#!/usr/bin/env python3
"""
Simple CoNLL-U format validator function.
Returns 1.0 if text conforms to strict CoNLL-U format, 0.0 otherwise.

Usage:
    from conllu_validator import is_valid_conllu
    score = is_valid_conllu(response_text)
"""

import re

def grade(sample, item) -> float:
    """
    Fast validation of CoNLL-U format.
    
    Args:
        sample: The sample data (not used in this validator)
        item: Dictionary containing the response text to validate
        
    Returns:
        1.0 if valid CoNLL-U format, 0.0 otherwise
    """
    # Extract text from item - for evaluation, the expected response is what should be validated
    text = item.get('expected_response', '') if isinstance(item, dict) else str(item)
    
    if not text or not text.strip():
        return 0.0
    
    lines = text.strip().split('\n')
    
    # Pattern for valid CoNLL-U line: 10 tab-separated fields
    conllu_pattern = re.compile(r'^([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]*)\t([^\t]*)\t([^\t]+)\t([^\t]+)\t([^\t]*)\t([^\t]*)$')
    
    token_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip comment lines (should not be present in our format)
        if line.startswith('#'):
            return 0.0
            
        # Check if line matches CoNLL-U format
        match = conllu_pattern.match(line)
        if not match:
            return 0.0
            
        # Extract fields
        token_id, form, lemma, upos, xpos, feats, head, deprel, deps, misc = match.groups()
        
        # Validate required fields are not empty
        if not form or not lemma or not upos or not deprel:
            return 0.0
            
        token_count += 1
    
    # Must have at least one token
    if token_count == 0:
        return 0.0
        
    return 1.0


