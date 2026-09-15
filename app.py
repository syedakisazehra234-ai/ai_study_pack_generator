import json
import os

import streamlit as st

from workflow import run, to_dict


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Study Pack Generator",
    page_icon="🎓",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title("🎓 AI Study Pack Generator")

st.caption(
    "Planning → Content Generation → Assessment → Review → Refinement"
)


# ============================================================
# GET GROQ API KEY
# ============================================================

def get_api_key():

    try:
        secret_key = st.secrets.get("GROQ_API_KEY", "")

        if secret_key:
            return secret_key

    except Exception:
        pass

    return os.getenv("GROQ_API_KEY", "")


# ============================================================
# RENDER FINAL STUDY PACK
# ============================================================

def render_study_pack(pack, sections):

    output = []

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    output.append(
        f"# {pack.get('title', 'AI Study Pack')}"
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    if "Summary" in sections:

        summary = pack.get("summary")

        if summary:
            output.append(
                "## 📚 Summary\n" + summary
            )

        key_points = pack.get("key_points", [])

        if key_points:
            output.append(
                "## 🔑 Key Points\n"
                + "\n".join(
                    f"- {point}"
                    for point in key_points
                )
            )

        examples = pack.get("examples", [])

        if examples:
            output.append(
                "## 💡 Examples\n"
                + "\n".join(
                    f"- {example}"
                    for example in examples
                )
            )

    # --------------------------------------------------------
    # FLASHCARDS
    # --------------------------------------------------------

    if "Flashcards" in sections:

        flashcards = pack.get("flashcards", [])

        if flashcards:

            cards = []

            for i, card in enumerate(flashcards, start=1):

                front = card.get("front", "")
                back = card.get("back", "")

                cards.append(
                    f"### Card {i}\n"
                    f"**Q:** {front}\n\n"
                    f"**A:** {back}"
                )

            output.append(
                "## 🧠 Flashcards\n"
                + "\n\n".join(cards)
            )

    # --------------------------------------------------------
    # QUIZ
    # --------------------------------------------------------

    if "Quiz" in sections:

        quiz = pack.get("quiz", [])

        if quiz:

            questions = []

            for i, question in enumerate(quiz, start=1):

                question_text = question.get(
                    "question",
                    ""
                )

                options = question.get(
                    "options",
                    []
                )

                answer = question.get(
                    "answer",
                    ""
                )

                explanation = question.get(
                    "explanation",
                    ""
                )

                option_text = "\n".join(
                    f"- {option}"
                    for option in options
                )

                questions.append(
                    f"### {i}. {question_text}\n\n"
                    f"{option_text}\n\n"
                    f"**Answer:** {answer}\n\n"
                    f"**Explanation:** {explanation}"
                )

            output.append(
                "## 📝 Quiz\n"
                + "\n\n".join(questions)
            )

    # --------------------------------------------------------
    # STUDY TIPS
    # --------------------------------------------------------

    study_tips = pack.get(
        "study_tips",
        []
    )

    if study_tips:

        output.append(
            "## 🎯 Study Tips\n"
            + "\n".join(
                f"- {tip}"
                for tip in study_tips
            )
        )

    return "\n\n".join(output)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Study Preferences")

    topic = st.text_input(
        "📖 Topic",
        placeholder="e.g. Photosynthesis"
    )

    level = st.selectbox(
        "🎓 Student Level",
        [
            "School",
            "High School",
            "College",
            "University",
            "Professional"
        ],
        index=1
    )

    language = st.selectbox(
        "🌐 Language",
        [
            "English",
            "Urdu",
            "Roman Urdu"
        ]
    )

    difficulty = st.select_slider(
        "⚡ Difficulty",
        options=[
            "Easy",
            "Medium",
            "Hard"
        ],
        value="Medium"
    )

    sections = st.multiselect(
        "📦 Sections",
        [
            "Summary",
            "Flashcards",
            "Quiz"
        ],
        default=[
            "Summary",
            "Flashcards",
            "Quiz"
        ]
    )

    num_questions = st.slider(
        "❓ Quiz Questions",
        min_value=3,
        max_value=20,
        value=5
    )

    extra_instructions = st.text_area(
        "➕ Extra Instructions",
        placeholder="e.g. Explain with simple examples"
    )

    generate = st.button(
        "🚀 Generate Study Pack",
        type="primary",
        use_container_width=True
    )


# ============================================================
# GENERATE STUDY PACK
# ============================================================

if generate:

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    if not topic.strip():

        st.warning(
            "⚠️ Please enter a topic."
        )

        st.stop()

    if not sections:

        st.warning(
            "⚠️ Please select at least one section."
        )

        st.stop()

    # --------------------------------------------------------
    # API KEY
    # --------------------------------------------------------

    api_key = get_api_key()

    if not api_key:

        st.error(
            "❌ GROQ_API_KEY is missing. "
            "Please add it to Streamlit Secrets."
        )

        st.stop()

    # --------------------------------------------------------
    # PROGRESS UI
    # --------------------------------------------------------

    progress_bar = st.progress(0)

    status = st.empty()

    def update_progress(stage_number, stage_name):

        progress_bar.progress(
            stage_number / 5
        )

        status.info(
            f"Stage {stage_number}/5 — **{stage_name}**"
        )

    # --------------------------------------------------------
    # RUN WORKFLOW
    # --------------------------------------------------------

    try:

        context = run(
            topic=topic,
            level=level,
            language=language,
            difficulty=difficulty,
            sections=sections,
            num_questions=num_questions,
            extra=extra_instructions,
            api_key=api_key,
            progress=update_progress
        )

    except Exception as error:

        st.error(
            f"❌ Unexpected error: {error}"
        )

        st.stop()

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    if context.refined_pack:

        progress_bar.progress(1.0)

        status.success(
            "All 5 AI stages completed successfully."
        )

        st.success(
            "🎉 Your study pack has been generated!"
        )

        tab1, tab2, tab3 = st.tabs(
            [
                "📚 Final Study Pack",
                "🔄 Workflow Trace",
                "🧩 Context"
            ]
        )

        # ====================================================
        # TAB 1 — FINAL STUDY PACK
        # ====================================================

        with tab1:

            study_pack_markdown = render_study_pack(
                context.refined_pack,
                sections
            )

            st.markdown(
                study_pack_markdown
            )

            st.download_button(
                label="⬇️ Download JSON",
                data=json.dumps(
                    context.refined_pack,
                    ensure_ascii=False,
                    indent=2
                ),
                file_name="study_pack.json",
                mime="application/json"
            )

        # ====================================================
        # TAB 2 — WORKFLOW TRACE
        # ====================================================

        with tab2:

            st.subheader(
                "5-Stage AI Workflow"
            )

            stages = [
                "Planning",
                "Content Generation",
                "Assessment",
                "Review",
                "Refinement"
            ]

            for stage in stages:

                if stage in context.completed:

                    st.success(
                        f"✅ {stage} completed"
                    )

                else:

                    st.warning(
                        f"⚠️ {stage} not completed"
                    )

            if context.errors:

                st.subheader(
                    "Validation Messages"
                )

                for error in context.errors:

                    st.warning(error)

        # ====================================================
        # TAB 3 — CONTEXT
        # ====================================================

        with tab3:

            st.json(
                to_dict(context)
            )

    # --------------------------------------------------------
    # FAILURE
    # --------------------------------------------------------

    else:

        st.error(
            "❌ Workflow failed."
        )

        if context.errors:

            for error in context.errors:

                st.warning(error)

        else:

            st.warning(
                "No detailed error was returned."
            )


# ============================================================
# WORKFLOW INFORMATION
# ============================================================

with st.expander("ℹ️ How the AI Workflow Works"):

    st.markdown(
        """
        **1. Planning**  
        Creates a personalized learning strategy.

        **2. Content Generation**  
        Uses the learning plan to create study material.

        **3. Assessment**  
        Generates quiz questions based on the content.

        **4. Review**  
        Checks accuracy, alignment, coverage,
        personalization, clarity, and quiz correctness.

        **5. Refinement**  
        Applies reviewer feedback and creates
        the final study pack.

        Each stage receives relevant context from
        the previous stages.
        """
    )
