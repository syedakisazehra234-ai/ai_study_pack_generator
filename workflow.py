import json
import re
import time

from dataclasses import dataclass, field, asdict
from typing import Optional

from groq import Groq

import prompts


# ============================================================
# CONFIGURATION
# ============================================================

MODEL = "openai/gpt-oss-120b"

# Your current Groq TPM limit is 8,000.
# Keep individual completions small.
MAX_OUTPUT_TOKENS = 1800


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

    # Direct JSON
    try:
        return json.loads(text)

    except json.JSONDecodeError:
        pass

    # Extract JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:

        return json.loads(
            text[start:end + 1]
        )

    raise ValueError(
        "Model did not return valid JSON."
    )


# ============================================================
# COMPACT JSON
# ============================================================

def compact_json(data, max_chars=6000):

    if data is None:
        return "{}"

    text = json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":")
    )

    if len(text) <= max_chars:
        return text

    return (
        text[:max_chars]
        + "...[TRUNCATED]"
    )


# ============================================================
# EXTRACT WAIT TIME FROM 429 ERROR
# ============================================================

def get_wait_time(error_message):

    match = re.search(
        r"try again in\s+([0-9.]+)s",
        error_message,
        re.IGNORECASE
    )

    if match:

        return float(match.group(1))

    # Safe default
    return 15.0


# ============================================================
# GROQ CALL WITH RATE-LIMIT RETRY
# ============================================================

def ai_call(
    client,
    prompt,
    temperature=0.2,
    retries=3
):

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

                # Keep completion small.
                max_completion_tokens=MAX_OUTPUT_TOKENS,

                response_format={
                    "type": "json_object"
                }
            )

            output = (
                response
                .choices[0]
                .message
                .content
            )

            return parse_json(output), None

        except Exception as error:

            last_error = str(error)

            # ------------------------------------------------
            # RATE LIMIT
            # ------------------------------------------------

            if "429" in last_error:

                wait_seconds = get_wait_time(
                    last_error
                )

                # Add a small safety buffer
                wait_seconds += 2

                if attempt < retries:

                    time.sleep(
                        wait_seconds
                    )

                    continue

            # ------------------------------------------------
            # OTHER ERROR
            # ------------------------------------------------

            if attempt < retries:

                time.sleep(
                    2 ** attempt
                )

                continue

    return None, last_error


# ============================================================
# QUIZ VALIDATION
# ============================================================

def quiz_errors(
    quiz,
    expected_count
):

    errors = []

    if not isinstance(quiz, list):

        return [
            "Quiz is not a list."
        ]

    if len(quiz) != expected_count:

        errors.append(
            f"Expected {expected_count} "
            f"questions; received {len(quiz)}."
        )

    for i, question in enumerate(
        quiz,
        start=1
    ):

        if not isinstance(
            question,
            dict
        ):

            errors.append(
                f"Question {i} is invalid."
            )

            continue

        options = question.get(
            "options",
            []
        )

        if len(options) != 4:

            errors.append(
                f"Question {i}: "
                f"exactly 4 options required."
            )

        answer = question.get(
            "answer"
        )

        if answer not in options:

            errors.append(
                f"Question {i}: "
                f"answer is not one of "
                f"the options."
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

        num_questions=int(
            num_questions
        ),

        extra_instructions=extra
    )

    client = Groq(
        api_key=api_key
    )


    # ========================================================
    # STAGE 1 — PLANNING
    # ========================================================

    if progress:
        progress(
            1,
            "Planning"
        )

    result, error = ai_call(

        client,

        prompts.plan(context),

        temperature=0.2
    )

    if error:

        context.errors.append(
            f"Planning failed: {error}"
        )

        return context

    context.plan = result

    context.completed.append(
        "Planning"
    )


    # ========================================================
    # STAGE 2 — CONTENT GENERATION
    # ========================================================

    if progress:
        progress(
            2,
            "Content Generation"
        )

    result, error = ai_call(

        client,

        prompts.content(context),

        temperature=0.3
    )

    if error:

        context.errors.append(
            f"Content Generation failed: {error}"
        )

        return context

    context.content = result

    context.completed.append(
        "Content Generation"
    )


    # ========================================================
    # STAGE 3 — ASSESSMENT
    # ========================================================

    if progress:
        progress(
            3,
            "Assessment"
        )

    result, error = ai_call(

        client,

        prompts.assessment(context),

        temperature=0.2
    )

    if error:

        context.errors.append(
            f"Assessment failed: {error}"
        )

        return context

    context.assessment = result

    context.completed.append(
        "Assessment"
    )

    context.errors.extend(

        quiz_errors(

            result.get(
                "quiz",
                []
            ),

            context.num_questions
        )
    )


    # ========================================================
    # STAGE 4 — REVIEW
    # ========================================================

    if progress:
        progress(
            4,
            "Review"
        )

    result, error = ai_call(

        client,

        prompts.review(context),

        temperature=0.1
    )

    if error:

        context.errors.append(
            f"Review failed: {error}"
        )

        return context

    context.review = result

    context.completed.append(
        "Review"
    )


    # ========================================================
    # STAGE 5 — REFINEMENT
    # ========================================================

    if progress:
        progress(
            5,
            "Refinement"
        )

    result, error = ai_call(

        client,

        prompts.refine(context),

        temperature=0.2
    )

    if error:

        context.errors.append(
            f"Refinement failed: {error}"
        )

        return context

    context.refined_pack = result

    context.completed.append(
        "Refinement"
    )


    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    if context.refined_pack:

        final_quiz = (
            context.refined_pack
            .get("quiz", [])
        )

        context.errors.extend(

            quiz_errors(

                final_quiz,

                context.num_questions
            )
        )

    return context


# ============================================================
# CONVERT TO DICTIONARY
# ============================================================

def to_dict(context):

    return asdict(context)
