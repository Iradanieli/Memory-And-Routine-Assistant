# Personal Memory and Routine Assistant

Flask web application for a person with memory difficulties. The app combines:

- A Bedrock Knowledge Base memory assistant for natural-language questions.
- A local CSV routine dashboard for events, tasks, and reminders.
- A caregiver page for adding structured events and tasks.
- Docker packaging so the app code and both CSV files are included in one image.

## Topic

Personal Memory and Routine Assistant.

The user can ask questions such as:

- Who is my son?
- Where do I live?
- What should I do if I feel confused?
- What should I bring to my clinic appointment?

## RAG Documents

The RAG documents are stored in S3 and connected to an existing Amazon Bedrock Knowledge Base. They are not stored in this application image.

Documents used:

- `family_and_relationships.md`
- `daily_routine.md`
- `important_places.md`
- `safety_and_reassurance_notes.md`
- `life_story.md`
- `caregiver_instructions.md`
- `appointment_preparation.md`

Knowledge Base ID: configured with `BEDROCK_KNOWLEDGE_BASE_ID`.

AWS Region: `us-east-2`

Inference profile ARN: configured with `BEDROCK_MODEL_ARN`.

## Local CSV Data

The routine database is included in the Docker image:

- `structured/events.csv`
- `structured/todos.csv`

The caregiver page updates these CSV files only. It does not update the S3 documents or sync the Bedrock Knowledge Base.

## Run Locally

Create a virtual environment, install dependencies, and start Flask:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open:

```text
http://localhost:5000
```

For Bedrock questions to work locally, configure AWS credentials with permission to call the Bedrock Knowledge Base.

## Docker

For local development, use Docker Compose. It builds the image, loads `.env`, mounts `structured/` so CSV edits are saved, and mounts your local AWS credentials for Bedrock:

```bash
docker compose up --build
```

Open:

```text
http://localhost:5001
```

Stop it with `Ctrl+C`.

If you want to run Docker manually, build one Docker image containing the Flask app and both CSV files:

```bash
docker build -t memory-routine-assistant .
```

Run it:

```bash
docker run --rm -p 5000:5000 \
  -v "$(pwd)/structured:/app/structured" \
  -v ~/.aws:/root/.aws:ro \
  -e AWS_REGION=us-east-2 \
  -e BEDROCK_KNOWLEDGE_BASE_ID=your-bedrock-knowledge-base-id \
  -e BEDROCK_MODEL_ARN=your-bedrock-inference-profile-arn \
  memory-routine-assistant
```

Open:

```text
http://localhost:5000
```

## EC2 Deployment Notes

Recommended AWS credential method:

Attach an IAM role to the EC2 instance with permission to call Bedrock Agent Runtime for the Knowledge Base. This avoids storing AWS access keys in the app or Docker image.

Typical EC2 flow:

```bash
sudo yum update -y
sudo yum install -y docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ec2-user
```

After reconnecting to the instance, copy or pull the project files, then run:

```bash
docker build -t memory-routine-assistant .
docker run -d --name memory-app -p 80:5000 \
  -v "$(pwd)/structured:/app/structured" \
  -e AWS_REGION=us-east-2 \
  -e BEDROCK_KNOWLEDGE_BASE_ID=your-bedrock-knowledge-base-id \
  -e BEDROCK_MODEL_ARN=your-bedrock-inference-profile-arn \
  memory-routine-assistant
```

Open the app with the EC2 public IP or public DNS:

```text
http://EC2_PUBLIC_IP
```

The EC2 security group must allow inbound HTTP traffic on port 80.

## Screenshots to Submit

- Bedrock Knowledge Base screen.
- Data source sync status.
- Flask app running in the browser.
- EC2 instance details.
- Public app page using the EC2 public IP or DNS.
- Docker container running, for example `docker ps`.
- One successful question-and-answer example.

## Cleanup Note

After testing, delete temporary AWS resources to avoid costs:

- Terminate the EC2 instance.
- Delete temporary security groups if created only for this project.
- Delete unused Docker images or containers from EC2.
- Delete any temporary S3 or Bedrock resources created only for testing.

Keep the existing S3 documents and Bedrock Knowledge Base only if they are still needed.
