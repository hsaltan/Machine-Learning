import tempfile
import os
from openai import OpenAI
import pdfplumber
from gensim.parsing.preprocessing import (
    preprocess_string,
    strip_tags,
    strip_punctuation,
    strip_non_alphanum,
    strip_multiple_whitespaces,
    remove_stopwords,
)
import boto3
import re
from docx import Document
import itertools
from datetime import datetime


# Create an S3 client
s3 = boto3.client("s3")


def put_object(bucket_name, file_name, file_object):

    # Save the uploaded file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(file_object.getvalue())
        temp_file_path = temp_file.name

    # Upload the file to S3
    with open(temp_file_path, "rb") as file:
        s3.upload_fileobj(file, bucket_name, file_name)

    # Remove the temporary file
    os.unlink(temp_file_path)

    message = (
        f"CV file '{file_name}' uploaded successfully to S3 bucket '{bucket_name}'!"
    )

    return message


def create_file_name(uploaded_cv_name, jd_title):

    # Get today's date
    today_date = datetime.today()

    # Format today's date as YYYY-MM-DD
    formatted_date = today_date.strftime("%Y-%m-%d")

    file_name = f"{formatted_date}-{jd_title}-{uploaded_cv_name}"

    return file_name


region = "us-east-1"


def get_parameter(parameter_name, with_decryption=False):
    """
    Retrieves a parameter from AWS Parameter Store to use it in the code.
    """

    response = boto3.client("ssm", region_name=region).get_parameter(
        Name=parameter_name, WithDecryption=with_decryption
    )
    parameter_value = response["Parameter"]["Value"]

    return parameter_value


OPENAI_KEY = get_parameter("openai-key", with_decryption=True)
client = OpenAI(api_key=OPENAI_KEY)


def adjust_response(answer):

    splitted_keywords = answer.split("\n")
    list_keywords = [
        splitted_keyword.replace("-", "").lower()
        for splitted_keyword in splitted_keywords
    ]
    filtered_list = list(filter(None, list_keywords))
    single_keywords = [element.split() for element in filtered_list]
    flattened_keywords = list(itertools.chain(*single_keywords))
    simplified_keywords = list(set(flattened_keywords))
    long_keywords = [
        simplified_keyword
        for simplified_keyword in simplified_keywords
        if len(simplified_keyword) > 3
    ]

    return long_keywords


def extract_keywords(text, temperature=0, max_tokens=100):

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are the HR manager. You will be provided with a block of text, and your task is to extract a list of keywords from it.",
            },
            {"role": "user", "content": text},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=1,
    )

    answer = response.choices[0].message.content

    keywords = adjust_response(answer)

    return keywords


def score_candidate(cv, job_description, max_tokens=200, temperature=0):

    prompt = f"""
        Review the following CV and job description, then score the suitability of the candidate for the job on a scale from 1 to 10, with 10 being the most matching CV score. 
        Please apply a critical analysis, being conservative in scoring. Scores should be expressed as floating-point numbers with two decimal places. 
        Use the following guidelines for scoring:
        - Score 8.50-10: Meets all job and education requirements with additional qualifications that exceed expectations.
        - Score 5-8.49: Meets most job and education requirements but lacks in one or two key areas. May have additional qualifications.
        - Score 2-4.99: Does not sufficiently meet the job and education requirements. Might have one or two relevant additional qualifications.
        - Score 0-1.99: Does not meet the job and education requirements at all. Does not have any relevant additional qualifications.
        Provide a balanced rationale for the score in 2-4 sentences, highlighting specific aspects of the CV that align or do not align with the job requirements. In your output, follow this format:
        CV: {cv}

        Job Description: {job_description}

        Score:

        Rationale:
        """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=1,
    )

    answer = response.choices[0].message.content

    return answer


def preprocess_text(text):

    lower_text = text.lower()
    tag_stripped_text = strip_tags(lower_text)
    punctuation_stripped_text = strip_punctuation(tag_stripped_text)
    non_alphanum_text = strip_non_alphanum(punctuation_stripped_text)
    mul_whitespace_stripped_text = strip_multiple_whitespaces(non_alphanum_text)
    clean_text = remove_stopwords(mul_whitespace_stripped_text)

    return clean_text


def remove_urls(text):
    # Regex pattern to match URLs
    url_pattern = r"https?://\S+|www\.\S+"
    # Replace URLs with an empty string
    cleaned_text = re.sub(url_pattern, "", text)
    return cleaned_text


def remove_pii(text):

    # Regex patterns for phone numbers, emails, and social media links
    patterns = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "phone": r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        "linkedin": r"https?://(www\.)?linkedin\.com/[\w-]+/[\w-]+",
        "github": r"https?://(www\.)?github\.com/[\w-]+",
        "stackoverflow": r"https?://(www\.)?stackoverflow\.com/[\w-]+",
        "kaggle": r"https?://(www\.)?kaggle\.com/[\w-]+",
    }

    for _, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            element = match.group()
            text = text.replace(element, "")

    return text


def pdf_to_oneline_string(file):

    with pdfplumber.open(file) as pdf:
        # Initialize an empty string to store the content
        text = ""

        # Iterate through each page and extract text
        for page in pdf.pages:
            text += page.extract_text()
    return text


def read_word_document(file):

    # Read the uploaded .docx file
    docx = Document(file)

    # Initialize an empty string to store the content
    text = ""

    # Iterate through each paragraph and extract text
    for paragraph in docx.paragraphs:
        text += paragraph.text + "\n"

    return text


def is_pdf(filename):
    return filename.lower().endswith(".pdf")


def is_word_document(filename):
    return filename.lower().endswith((".doc", ".docx"))


def open_file(path, file):
    if is_pdf(path):
        single_line_text = pdf_to_oneline_string(file)
    elif is_word_document(path):
        single_line_text = read_word_document(file)
    else:
        print("This is neither a PDF nor a Word document.")
    return single_line_text
