"""Prompt construction for Module 4 (LLM querying).

Template is fixed by the project plan (SFP_coding plan.md, section 5, Module 4).
"""

PROMPT_TEMPLATE = """阅读下面的对话情景，判断说话人的态度，只输出选项字母。

情景：{context}
句子："{sentence}"
问题：{question}

选项：
A) {opt_a}
B) {opt_b}
C) {opt_c}
D) {opt_d}

答案："""

# Context-only ablation variant (see src/ablation/): identical instruction
# wording, options block, and output-format ending -- the 句子 line is
# dropped entirely (not left blank) since there is no target sentence to
# show in this condition. Kept in this module, next to the main template,
# so there is exactly one place prompt wording lives for both the main
# experiment and its ablation, per the project's "reuse the pipeline, don't
# fork it" rule for this analysis step.
PROMPT_TEMPLATE_CONTEXT_ONLY = """阅读下面的对话情景，判断说话人的态度，只输出选项字母。

情景：{context}
问题：{question}

选项：
A) {opt_a}
B) {opt_b}
C) {opt_c}
D) {opt_d}

答案："""


def build_prompt(item: dict) -> str:
    """Build the prompt string for one item.

    `item` must have: context, sentence, question, options{A,B,C,D}.
    """
    options = item["options"]
    return PROMPT_TEMPLATE.format(
        context=item["context"],
        sentence=item["sentence"],
        question=item["question"],
        opt_a=options["A"],
        opt_b=options["B"],
        opt_c=options["C"],
        opt_d=options["D"],
    )


def build_context_only_prompt(item: dict) -> str:
    """Ablation variant of build_prompt(): same item shape minus `sentence`
    (not read, so items need not even carry it).
    """
    options = item["options"]
    return PROMPT_TEMPLATE_CONTEXT_ONLY.format(
        context=item["context"],
        question=item["question"],
        opt_a=options["A"],
        opt_b=options["B"],
        opt_c=options["C"],
        opt_d=options["D"],
    )
