# Benchmark attribution and adaptations

HumanEval: OpenAI, Chen et al., *Evaluating Large Language Models Trained on
Code*, https://github.com/openai/human-eval , MIT (sources/humaneval_LICENSE).
The source revision and data hashes are in sources/retrieval.json. Upstream
marks the legacy project deprecated/unmaintained. Official test strings are
preserved; reference docstrings are removed only in the supervised teaching
program, with original canonical strings retained in taught.json.

MBPP: Google Research, Austin et al., *Program Synthesis with Large Language
Models*, https://github.com/google-research/google-research/tree/master/mbpp .
Dataset card identifies CC BY4.0, retained at sources/mbpp_card.md. Credit the
dataset authors; selected original prompts, code and three tests are preserved.
The evaluation input adds the required function signature as interface metadata.
No reference body or private test is part of its generation input.

This is a selected8+8 local pilot with chat prompts and sandboxed Python3.12,
not official aggregate HumanEval/MBPP results. Using HumanEval reference answers
in weight construction intentionally contaminates its taught subset. MBPP
solutions are used only by reference validation/evaluation, never weight edits.
