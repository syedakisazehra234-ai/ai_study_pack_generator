import json


SYSTEM = """
You are a precise educational AI.

Rules:
1. Return ONLY valid JSON.
2. Do not use markdown.
3. Do not add explanations outside JSON.
4. Follow the requested structure exactly.
5. Keep responses concise.
"""


def plan(c):

    return f"""
Create a personalized learning plan.

Topic: {c.topic}
Student level: {c.level}
Language: {c.language}
Difficulty: {c.difficulty}

Requested sections:
{", ".join(c.sections)}

Number of quiz questions:
{c.num_questions}

Extra instructions:
{c.extra_instructions or "None"}

Return ONLY this JSON structure:

{{
  "learning_goal": "",
  "learner_profile": "",
  "subtopics": [],
  "prerequisites": [],
  "priority_concepts": [],
  "recommended_sequence": [],
  "content_strategy": "",
  "assessment_strategy": ""
}}

Keep the plan concise.
"""


def content(c):

    plan = json.dumps(
        c.plan,
        ensure_ascii=False,
        separators=(",", ":")
    )

    return f"""
Create study content using this learning plan.

Topic: {c.topic}
Level: {c.level}
Language: {c.language}
Difficulty: {c.difficulty}

Learning plan:
{plan}

Requested sections:
{", ".join(c.sections)}

Do NOT create quiz questions.

Return ONLY this JSON:

{{
  "title": "",
  "summary": "",
  "key_points": [],
  "flashcards": [
    {{
      "front": "",
      "back": ""
    }}
  ],
  "examples": []
}}

Keep the content focused and concise.
"""


def assessment(c):

    plan = json.dumps(
        c.plan,
        ensure_ascii=False,
        separators=(",", ":")
    )

    content = json.dumps(
        c.content,
        ensure_ascii=False,
        separators=(",", ":")
    )

    return f"""
Create exactly {c.num_questions} multiple-choice questions.

Topic:
{c.topic}

Difficulty:
{c.difficulty}

Learning plan:
{plan}

Study content:
{content}

Every question MUST have:

- question
- exactly 4 options
- answer
- explanation
- tested_concept
- difficulty

The answer MUST exactly match one of the four options.

Return ONLY:

{{
  "quiz": [],
  "assessment_coverage": []
}}

Keep explanations concise.
"""


def review(c):

    plan = json.dumps(
        c.plan,
        ensure_ascii=False,
        separators=(",", ":")
    )

    content = json.dumps(
        c.content,
        ensure_ascii=False,
        separators=(",", ":")
    )

    assessment = json.dumps(
        c.assessment,
        ensure_ascii=False,
        separators=(",", ":")
    )

    return f"""
Review this educational study pack.

Topic:
{c.topic}

Plan:
{plan}

Content:
{content}

Assessment:
{assessment}

Check:

1. Accuracy
2. Alignment with learning goals
3. Coverage
4. Personalization
5. Clarity
6. Quiz correctness
7. Difficulty consistency

Return ONLY:

{{
  "overall_quality": "",
  "accuracy_issues": [],
  "personalization_issues": [],
  "coverage_issues": [],
  "assessment_issues": [],
  "clarity_issues": [],
  "required_changes": [],
  "approved": true
}}

Keep the review concise.
"""


def refine(c):

    # --------------------------------------------------------
    # IMPORTANT:
    # We intentionally keep the previous context compact.
    # This prevents the Refinement request from exceeding
    # Groq's 8K TPM limit.
    # --------------------------------------------------------

    plan = json.dumps(
        c.plan,
        ensure_ascii=False,
        separators=(",", ":")
    )

    content = json.dumps(
        c.content,
        ensure_ascii=False,
        separators=(",", ":")
    )

    assessment = json.dumps(
        c.assessment,
        ensure_ascii=False,
        separators=(",", ":")
    )

    review = json.dumps(
        c.review,
        ensure_ascii=False,
        separators=(",", ":")
    )

    return f"""
Create the FINAL study pack.

Topic:
{c.topic}

Student level:
{c.level}

Language:
{c.language}

Difficulty:
{c.difficulty}

Requested sections:
{", ".join(c.sections)}

Required quiz questions:
{c.num_questions}

Learning plan:
{plan}

Study content:
{content}

Assessment:
{assessment}

Reviewer feedback:
{review}

Apply the reviewer's required changes.

The final pack must contain:

- title
- summary
- key_points
- flashcards
- examples
- quiz
- study_tips

Quiz requirements:

- exactly {c.num_questions} questions
- exactly 4 options per question
- answer must exactly match one option
- concise explanations

Return ONLY valid JSON.

Do not include markdown.
"""
