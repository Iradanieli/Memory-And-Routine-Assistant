import os
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError


AWS_REGION = os.getenv("AWS_REGION", "")
BEDROCK_AGENT_ID = os.getenv("BEDROCK_AGENT_ID", "").strip().strip("\"'")
BEDROCK_AGENT_ALIAS_ID = os.getenv("BEDROCK_AGENT_ALIAS_ID", "").strip().strip("\"'")
BEDROCK_AGENT_SESSION_ID = (
    os.getenv("BEDROCK_AGENT_SESSION_ID", "memory-assistant-session")
    .strip()
    .strip("\"'")
)


def read_agent_completion(response):
    answer_parts = []
    citations = []

    for event in response.get("completion", []):
        chunk = event.get("chunk")
        if chunk:
            bytes_payload = chunk.get("bytes")
            if bytes_payload:
                answer_parts.append(bytes_payload.decode("utf-8"))

            attribution = chunk.get("attribution")
            if attribution:
                for citation in attribution.get("citations", []):
                    for reference in citation.get("retrievedReferences", []):
                        location = reference.get("location", {})
                        s3_location = location.get("s3Location", {})
                        uri = s3_location.get("uri")
                        if uri:
                            citations.append(uri)

    return "".join(answer_parts), citations


def clean_answer_text(value):
    return (
        (value or "")
        .replace("\\*", "*")
        .replace("**", "")
        .replace("*", "")
        .replace("∗", "")
        .replace("＊", "")
        .replace("﹡", "")
        .strip()
    )


def ask_bedrock_agent(question):
    if not BEDROCK_AGENT_ID or not BEDROCK_AGENT_ALIAS_ID:
        return (
            "Bedrock Agent configuration is missing. Set BEDROCK_AGENT_ID "
            "and BEDROCK_AGENT_ALIAS_ID in the environment.",
            [],
        )

    client = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
    response = client.invoke_agent(
        agentId=BEDROCK_AGENT_ID,
        agentAliasId=BEDROCK_AGENT_ALIAS_ID,
        sessionId=BEDROCK_AGENT_SESSION_ID,
        inputText=question,
    )
    answer, citations = read_agent_completion(response)

    answer = clean_answer_text(answer)

    return answer or "I could not find an answer in the memory documents.", citations


def answer_question(payload):
    question = payload.get("question", "").strip()

    if not question:
        return {"error": "Please type a question first."}, 400

    try:
        answer, citations = ask_bedrock_agent(question)
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
