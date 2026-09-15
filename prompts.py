import json


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM = """
You are a precise educational AI.

Rules:

1. Return ONLY valid JSON.
2. Never use markdown outside JSON.
3. Follow the requested JSON structure.
4. Keep responses concise.
5. Do not repeat unnecessary information.
"""


# ============================================================
# PLANNING
# ============================================================

def plan(c):

    return f"""
Create a personalized learning plan.

Topic: {c.topic}
Level: {c.level}
Language: {c.language}
Difficulty: {c.difficulty}

Requested sections:
{", ".join(c.sections)}

Quiz questions:
{c.num_questions}

Extra instructions:
{c.extra_instructions or "None"}

Return:

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

Keep it concise.
"""


# ============================================================
# CONTENT
# ============================================================

def content(c):

    plan = json.dumps(
        c.plan,
        ensure_ascii=False,
        separators=(",", ":")
    )

    return f"""
Create concise study content.

Topic: {c.topic}
Level: {c.level}
Language: {c.language}
Difficulty: {c.difficulty}

Learning plan:
{plan}

Requested sections:
{", ".join(c.sections)}

Do NOT create quiz questions.

Return:

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

Keep explanations concise.
"""


# ============================================================
# ASSESSMENT
# ============================================================

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
Create exactly {c.num_questions} MCQs.

Topic:
{c.topic}

Difficulty:
{c.difficulty}

Plan:
{plan}

Content:
{content}

Each question MUST contain:

question
options
answer
explanation
tested_concept
difficulty

Rules:

- exactly 4 options
- answer must match one option
- concise explanations

Return ONLY:

{{
  "quiz": [],
  "assessment_coverage": []
}}
"""


# ============================================================
# REVIEW
# ============================================================

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
Review this study pack.

Topic:
{c.topic}

Plan:
{plan}

Content:
{content}

Assessment:
{assessment}

Check:

- accuracy
- learning alignment
- coverage
- personalization
- clarity
- quiz correctness

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


# ============================================================
# REFINEMENT
# ============================================================

def refine(c):

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # We do NOT send the complete assessment back.
    #
    # The final refinement mainly needs:
    # - original topic
    # - learning plan
    # - generated content
    # - reviewer feedback
    #
    # This dramatically reduces token usage.
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

    review = json.dumps(
        c.review,
        ensure_ascii=False,
        separators=(",", ":")
    )

    return f"""
Create the FINAL study pack.

Topic:
{c.topic}

Level:
{c.level}

Language:
{c.language}

Difficulty:
{c.difficulty}

Requested sections:
{", ".join(c.sections)}

Number of quiz questions:
{c.num_questions}

Learning plan:
{plan}

Study content:
{content}

Reviewer feedback:
{review}

Apply all required reviewer changes.

Return ONLY:

{{
  "title": "",
  "summary": "",
  "key_points": [],
  "flashcards": [],
  "examples": [],
  "quiz": [],
  "study_tips": []
}}

Quiz rules:

- exactly {c.num_questions} questions
- exactly 4 options each
- answer must match an option
- concise explanations

Keep the final response concise.
"""
