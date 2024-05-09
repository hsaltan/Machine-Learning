import streamlit as st
import cvanalyzer


def main():

    st.title("CV Screening Assistant")

    st.header("AI-powered CV Screening and Analysis")

    st.image("HR_image_1.png")

    st.write("")
    st.write("")
    st.write("")

    # Create a file uploader widget
    uploaded_cv = st.file_uploader("CV Upload (.pdf, .docx)*")

    st.write("")
    st.write("")

    # Create a file uploader widget
    uploaded_jd = st.file_uploader("Job Description Upload (.pdf, .docx)*")

    st.write("")
    st.write("")

    jd_title = st.text_input(
        "Enter the job title (e.g. Machine learning engineer, history teacher, etc.) - optional"
    )

    if jd_title:
        jd_title = jd_title.strip().lower()
        jd_title = jd_title.replace(" ", "-")
    else:
        jd_title = "untitled"

    st.write("")
    st.write("")

    # Add widgets
    button = st.button("Submit")

    st.write("")
    st.write("")

    if button:
        if uploaded_cv is not None and uploaded_jd is not None:
            uploaded_cv_name = uploaded_cv.name
            opened_cv_file_text = cvanalyzer.open_file(uploaded_cv_name, uploaded_cv)
            cv_text_without_pii = cvanalyzer.remove_pii(opened_cv_file_text)
            cv_text_without_urls = cvanalyzer.remove_urls(cv_text_without_pii)
            final_cv_text = cvanalyzer.preprocess_text(cv_text_without_urls)

            uploaded_jd_name = uploaded_jd.name
            jd_text = cvanalyzer.open_file(uploaded_jd_name, uploaded_jd)
            final_jd_text = cvanalyzer.preprocess_text(jd_text)

            cv_result = cvanalyzer.score_candidate(
                final_cv_text, jd_text, max_tokens=200, temperature=0
            )

            cv_result = cv_result.replace("\n", "<br>")

            keywords = cvanalyzer.extract_keywords(
                final_jd_text, temperature=0, max_tokens=100
            )

            style = "background-color: #7aecec; color: black; padding: 0.2em 0.4em; border-radius: 8px;"

            opened_cv_file_text = opened_cv_file_text.replace("\n", "<br>")

            for keyword in keywords:
                opened_cv_file_text = opened_cv_file_text.replace(
                    keyword, f'<span style="{style}">{keyword}</span>'
                )

            st.subheader("Score and Rationale", divider="grey")

            st.markdown(
                f"<span style='font-size:20px'>{cv_result}</span>",
                unsafe_allow_html=True,
            )

            st.write("")
            st.write("")

            st.subheader("Keywords", divider="grey")

            # Display the highlighted text
            st.markdown(
                f"<span style='font-size:20px'>{opened_cv_file_text}</span>",
                unsafe_allow_html=True,
            )

            st.write("")
            st.write("")

            st.subheader("Save", divider="grey")
            st.write("Shall I save the CV for future analysis? - optional")
            st.write(
                "Clicking the button will upload the CV file to your dedicated bucket."
            )

            st.write("")
            st.write("")

            def click_button():
                file_name = cvanalyzer.create_file_name(uploaded_cv_name, jd_title)
                bucket_name = "selected-cvs"
                message = cvanalyzer.put_object(bucket_name, file_name, uploaded_cv)

            st.button("Yes", on_click=click_button)

    m = st.markdown(
        """
    <style>
    div.stButton > button:first-child {
        background-color: #206893;
        color:#ffffff;
    }
    div.stButton > button:hover {
        background-color: #ACCBDA;
        color:#215273;
        }
    </style>""",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
