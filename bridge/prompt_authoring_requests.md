# Prompt Authoring Requests

Use these requests with another strong language model to generate full prompt content for this repo.

The goal is not to get short one-line prompts. The goal is to get production-grade prompt text that can later be dropped into `bridge/snippets.yml` and `bridge/prompts.yml`.

## 1. Prompt Picker Request

```text
You are helping author a reusable prompt library for a keyboard-driven prompt picker.

I need you to generate full, high-quality prompt texts for a prompt snippet library. These prompts will be stored in YAML and copied directly to the clipboard when selected. They are not assistant responses. They are reusable user prompts intended to be pasted into another language model.

The current snippet categories are:
- Prompting
- Email
- Explanation
- Writing
- Analysis
- Code
- Translation
- Creative

The current snippet names are:

Prompting:
- Expand this properly
- Improve this prompt

Email:
- Write this email
- Reply to this email
- Follow up on this

Explanation:
- Explain this like I'm 10

Writing:
- Make this concise
- Improve the writing
- Make this more formal
- Make this more natural

Analysis:
- Summarize the key points
- Extract action items
- Turn this into meeting notes
- Write a decision memo

Code:
- Review this code
- Explain this code
- Turn this into a bug report
- Refactor this code
- Write tests for this

Translation:
- Translate Danish to English
- Translate English to Danish

Creative:
- Brainstorm strong options

What I need from you:

For each snippet name above, write a complete, production-quality prompt text that is substantially better than a short placeholder.

Requirements:

1. These prompts are meant for copy-paste use with another LLM.
2. Each prompt should be self-contained and directly usable.
3. Each prompt should clearly define:
   - the role the model should take
   - the task to perform
   - quality standards
   - constraints
   - how to handle ambiguity or missing information
   - the desired output format
4. Prompts should be practical, direct, and high-quality, not bloated for its own sake.
5. The prompts should generally preserve user intent and be helpful in real work settings.
6. Avoid generic filler like “be helpful” or “do your best” unless made concrete.
7. Do not write tiny prompts. Make them detailed enough to actually improve output quality.
8. Do not add XML, JSON, or code fences inside the prompt texts unless clearly necessary.
9. Keep the prompts suitable for everyday keyboard workflow use.
10. Use the same language as the input unless the task is explicitly a translation task.

Important style guidance:

- For Email prompts, optimize for Danish/Nordic professional tone: calm, direct, clear, non-hype, non-American-corporate.
- For Code prompts, prioritize correctness, risks, regressions, edge cases, and practical implementation detail.
- For Analysis prompts, optimize for decision usefulness, not pretty summaries.
- For Prompting prompts, optimize for stronger downstream model performance without changing the user’s core goal.
- For Translation prompts, preserve tone, terminology, and intent, and avoid over-literal output.
- For Writing prompts, preserve meaning unless explicitly told to expand or reshape it.

Output format:

Return a YAML-ready block in this exact structure:

snippets:
  - name: <exact snippet name>
    category: <exact category>
    text: |
      <full prompt text>

Rules for output:

- Use the exact snippet names listed above.
- Use the exact category labels listed above.
- Keep the same ordering as provided above.
- Return only the YAML content.
- Do not explain anything before or after the YAML.
```

## 2. LLM Prompt Template Request

```text
You are helping author production-grade LLM prompt templates for a keyboard-driven AI text transformation system.

These prompts will live in a YAML file and will be used by a bridge daemon that sends selected text through an LLM. Each prompt must be written as a reusable template with `${text}` as the runtime insertion point.

The active prompt keys that need full, production-grade templates are:
- improve_writing
- write_email
- prompt_expand
- fix_grammar
- summarize
- translate_da_en
- translate_en_da
- stt_postprocess

Each template is used for a different keyboard action:

- improve_writing: improve selected writing while preserving meaning and appropriate tone
- write_email: turn selected text into a polished professional email for a Danish/Nordic work context
- prompt_expand: transform highlighted user instructions into stronger prompts for another LLM
- fix_grammar: lightly correct spelling, grammar, punctuation, and obvious minor issues only
- summarize: produce a concise useful summary
- translate_da_en: translate Danish to English
- translate_en_da: translate English to Danish
- stt_postprocess: clean up speech-to-text transcript output without changing intended meaning

What I need from you:

Write a high-quality prompt template for each prompt key above.

Requirements:

1. Each prompt must be written as YAML-ready multi-line text.
2. Each prompt must include `${text}` as the insertion point.
3. Each prompt should clearly define:
   - the model’s role
   - the exact transformation objective
   - what must be preserved
   - what may be changed
   - output constraints
   - ambiguity handling rules
4. Prompts must be strong enough for production use, not short placeholders.
5. The prompt should optimize for reliable outputs from a capable but not perfect LLM.
6. Unless the task explicitly calls for transformation, preserve meaning, facts, tone, and intent.
7. Each prompt should end in a way that strongly discourages commentary, preambles, or explanations unless the task explicitly requires them.
8. Do not include chain-of-thought requests.
9. Do not add unnecessary verbosity.
10. Make the prompts practical and robust.

Task-specific guidance:

improve_writing:
- Improve clarity, flow, structure, and wording.
- Preserve core meaning and appropriate tone.
- Do not overrewrite into a different voice unless needed.

write_email:
- Optimize for Danish/Nordic professional communication.
- Calm, clear, direct, competent tone.
- Avoid hype, exaggerated politeness, and American corporate style.
- Include a relevant subject line, greeting, body, closing, and sign as Kristian Bilstrup.

prompt_expand:
- Strengthen a user instruction for another LLM.
- Preserve the original goal and deliverable.
- Increase rigor, clarity, completeness, verification expectations, and specificity.
- Return only the rewritten prompt.

fix_grammar:
- Make the smallest necessary changes.
- Fix correctness, not style drift.
- Preserve original wording as much as possible.

summarize:
- Optimize for decision usefulness.
- Capture the most important points and omit noise.
- Keep it concise.

translate_da_en / translate_en_da:
- Preserve tone, terminology, register, and intended meaning.
- Prefer fluent natural output over literal awkward wording.
- Do not explain translation choices.

stt_postprocess:
- The input is a transcript, potentially noisy.
- Fix obvious transcript errors, punctuation, formatting, and casing.
- Preserve the speaker’s intended meaning.
- Do not embellish or add content.
- If the text is ambiguous, prefer conservative correction over aggressive rewriting.

Output format:

Return YAML entries only, in this exact style:

<prompt_key>: |
  <prompt text>

Use the exact prompt keys listed above.
Keep the same ordering.
Return only the YAML content.
Do not include any explanation before or after the YAML.
```

## 3. Optional Follow-Up Request For Expanding The Library

If I later want to fill the currently unconfigured action keys, I will ask for additional prompt templates for likely future actions such as:
- explain_code
- review_code
- bug_report
- extract_actions
- meeting_notes
- decision_memo
- make_formal
- make_natural
- brainstorm_options

But for now, generate only the currently listed active keys and snippet names.
