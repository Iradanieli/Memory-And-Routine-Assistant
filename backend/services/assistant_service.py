import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError


AWS_REGION = os.getenv("AWS_REGION", "")
KNOWLEDGE_BASE_ID = os.getenv("BEDROCK_KNOWLEDGE_BASE_ID", "")
BEDROCK_MODEL_ARN = os.getenv("BEDROCK_MODEL_ARN", "")
RAG_PROMPT_TEMPLATE = """
You are a calm and helpful memory assistant for a person with memory difficulties.

Use only the information in the search results to answer the user's question.

Rules:
1. Answer using only the provided search results.
2. If the search results do not contain enough information, say:
   "I do not have enough information in the memory documents."
3. Keep the answer simple, clear, and reassuring.
4. Do not invent facts.
5. If the question is about safety, confusion, appointments, family, places, or routine, answer gently and directly.

Search results:
$search_results$

Question:
$query$

Answer:
"""


def ask_knowledge_base(question):
    if not KNOWLEDGE_BASE_ID or not BEDROCK_MODEL_ARN:
        return (
            "Bedrock configuration is missing. Set BEDROCK_KNOWLEDGE_BASE_ID "
            "and BEDROCK_MODEL_ARN in the environment.",
            [],
        )

    client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
    response = client.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                "modelArn": BEDROCK_MODEL_ARN,
                "generationConfiguration": {
                    "promptTemplate": {
                        "textPromptTemplate": RAG_PROMPT_TEMPLATE,
                    },
                },
            },
        },
    )

    answer = response.get("output", {}).get("text", "")
    citations = []
    for citation in response.get("citations", []):
        for reference in citation.get("retrievedReferences", []):
            location = reference.get("location", {})
            s3_location = location.get("s3Location", {})
            uri = s3_location.get("uri")
            if uri:
                citations.append(uri)

    return answer or "I could not find an answer in the memory documents.", citations


def answer_question(payload):
    question = payload.get("question", "").strip()

    if not question:
        return {"error": "Please type a question first."}, 400

    try:
        answer, citations = ask_knowledge_base(question)
    except NoCredentialsError:
        answer = (
            "AWS credentials were not found. On EC2, attach an IAM role with Bedrock "
            "permissions to the instance, then restart the container."
        )
        citations = []
    except (BotoCoreError, ClientError) as exc:
        answer = f"Bedrock could not answer right now: {exc}"
        citations = []

    return {"answer": answer, "citations": citations}, 200
