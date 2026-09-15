import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from groq import Groq
import prompts


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "openai/gpt-oss-120b"

# IMPORTANT:
# Your current Groq limit is 8,000 TPM.
# Keep completion requests comfortably below that.
MAX_OUTPUT_TOKENS = 3000


# ============================================================
# CONTEXT
# ============================================================

@dataclass
class Context:
    topic: str
    level: str
    language: str
    difficulty: str
    sections: list
    num_questions: int
    extra_instructions: str

    plan: Optional[dict] = None
    content: Optional[dict] = None
    assessment: Optional[dict] = None
    review: Optional[dict] = None
    refined_pack: Optional[dict] = None

    errors: list = field(default_factory=list)
    completed: list = field(default_factory=list)


# ============================================================
# JSON PARSER
# ============================================================

def parse_json(text):
    """
    Safely extract JSON from model response.
    Handles:
    - normal JSON
    - ```json ... ```
    - extra text before/after JSON
    """

    if not text:
        raise ValueError("Empty model response.")

    text = text.strip()

    # Remove markdown code fences
    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    # First attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return json.loads(text[start:end + 1])

    raise ValueError("Model did not return valid JSON.")


# ============================================================
# COMPACT JSON
# ============================================================

def compact_json(data, max_chars=9000):
    """
    Convert data to compact JSON.

    If it is too large, trim it so later stages don't
    create oversized Groq requests.
    """

    if data is None:
        return "{}"

    text = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":")
    )

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "...[TRUNCATED]"


# ============================================================
# GROQ CALL
# ============================================================

def ai_call(client, prompt, temperature=0.2, retries=2):

    last_error = "Unknown error"

    for attempt in range(retries + 1):

        try:

            response = client.chat.completions.create(
                model=MODEL,

                messages=[
                    {
                        "role": "system",
                        "content": prompts.SYSTEM
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=temperature,

                # IMPORTANT:
                # Previously this was 7000.
                # That caused the 8000 TPM error.
                max_completion_tokens=MAX_OUTPUT_TOKENS,

                # Ask Groq for valid JSON.
                response_format={
                    "type": "json_object"
                }
            )

            output = response.choices[0].message.content

            return parse_json(output), None

        except Exception as e:

            last_error = str(e)

    return None, last_error


# ============================================================
# QUIZ VALIDATION
# ============================================================

def quiz_errors(quiz, expected_count):

    errors = []

    if not isinstance(quiz, list):
        return ["Quiz is not a list."]

    if len(quiz) != expected_count:

        errors.append(
            f"Expected {expected_count} questions; "
            f"received {len(quiz)}."
        )

    for i, question in enumerate(quiz, start=1):

        if not isinstance(question, dict):
            errors.append(
                f"Question {i} is not a valid object."
            )
            continue

        options = question.get("options", [])

        if len(options) != 4:

            errors.append(
                f"Question {i}: exactly 4 options required."
            )

        answer = question.get("answer")

        if answer not in options:

            errors.append(
                f"Question {i}: answer is not one of the options."
            )

    return errors


# ============================================================
# MAIN WORKFLOW
# ============================================================

def run(
    topic,
    level,
    language,
    difficulty,
    sections,
    num_questions,
    extra,
    api_key,
    progress=None
):

    context = Context(
        topic=topic,
        level=level,
        language=language,
        difficulty=difficulty,
        sections=sections,
        num_questions=int(num_questions),
        extra_instructions=extra
    )

    client = Groq(api_key=api_key)

    # ========================================================
    # STAGE 1 — PLANNING
    # ========================================================

    if progress:
        progress(1, "Planning")

    plan_prompt = prompts.plan(context)

    result, error = ai_call(
        client,
        plan_prompt,
        temperature=0.2
    )

    if error:

        context.errors.append(
            f"Planning failed: {error}"
        )

        return context

    context.plan = result
    context.completed.append("Planning")


    # ========================================================
    # STAGE 2 — CONTENT GENERATION
    # ========================================================

    if progress:
        progress(2, "Content Generation")

    content_prompt = prompts.content(context)

    result, error = ai_call(
        client,
        content_prompt,
        temperature=0.3
    )

    if error:

        context.errors.append(
            f"Content Generation failed: {error}"
        )

        return context

    context.content = result
    context.completed.append("Content Generation")


    # ========================================================
    # STAGE 3 — ASSESSMENT
    # ========================================================

    if progress:
        progress(3, "Assessment")

    assessment_prompt = prompts.assessment(context)

    result, error = ai_call(
        client,
        assessment_prompt,
        temperature=0.2
    )

    if error:

        context.errors.append(
            f"Assessment failed: {error}"
        )

        return context

    context.assessment = result
    context.completed.append("Assessment")

    # Validate quiz
    quiz = result.get("quiz", [])

    context.errors.extend(
        quiz_errors(
            quiz,
            context.num_questions
        )
    )


    # ========================================================
    # STAGE 4 — REVIEW
    # ========================================================

    if progress:
        progress(4, "Review")

    review_prompt = prompts.review(context)

    result, error = ai_call(
        client,
        review_prompt,
        temperature=0.1
    )

    if error:

        context.errors.append(
            f"Review failed: {error}"
        )

        return context

    context.review = result
    context.completed.append("Review")


    # ========================================================
    # STAGE 5 — REFINEMENT
    # ========================================================

    if progress:
        progress(5, "Refinement")

    refinement_prompt = prompts.refine(context)

    result, error = ai_call(
        client,
        refinement_prompt,
        temperature=0.2
    )

    if error:

        context.errors.append(
            f"Refinement failed: {error}"
        )

        return context

    context.refined_pack = result
    context.completed.append("Refinement")


    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    if context.refined_pack:

        final_quiz = context.refined_pack.get(
            "quiz",
            []
        )

        context.errors.extend(
            quiz_errors(
                final_quiz,
                context.num_questions
            )
        )

    return context


# ============================================================
# CONVERT CONTEXT TO DICT
# ============================================================

def to_dict(context):
    return asdict(context)
