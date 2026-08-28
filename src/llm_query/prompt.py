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
