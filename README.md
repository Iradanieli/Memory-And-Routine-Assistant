# Personal Memory and Routine Assistant

Three-container web application for a person with memory difficulties. The app combines:

- A Bedrock Agent memory assistant for natural-language questions.
- A PostgreSQL routine database for events, tasks, and reminders.
- A caregiver page for adding structured events and tasks.
- A Flask backend API container.
- A PostgreSQL database container.
- An Nginx frontend container that serves the UI and proxies `/api` requests to the backend.

## Topic

Personal Memory and Routine Assistant.

The user can ask questions such as:

- Who is my son?
- Where do I live?
- What should I do if I feel confused?
- What should I bring to my clinic appointment?

## Submission Summary

Topic chosen: Personal Memory and Routine Assistant.

Public URL used during EC2 testing:

```text
http://3.144.148.97
```

The app was deployed as Docker containers on EC2:

- `memory-routine-frontend`: Nginx frontend container, publicly exposed on port `80`.
- `memory-routine-backend`: Flask backend API container, private inside the Docker network on port `5000`.
- `database`: PostgreSQL container, private inside the Docker network.

The frontend sends `/api/...` requests to Nginx, and Nginx proxies them to the backend container.

## Bedrock Agent And RAG Documents

The RAG documents are stored in S3 and connected to an existing Amazon Bedrock Knowledge Base. An Amazon Bedrock Agent uses that Knowledge Base and its configured Lambda action groups to answer questions. The documents and agent configuration are not stored in this application image.

Documents used:

- `family_and_relationships.md`
- `daily_routine.md`
- `important_places.md`
- `safety_and_reassurance_notes.md`
- `life_story.md`
- `caregiver_instructions.md`
- `appointment_preparation.md`

Agent ID: configured with `BEDROCK_AGENT_ID`.

AWS Region: `us-east-2`

Agent alias ID: configured with `BEDROCK_AGENT_ALIAS_ID`.

## Routine Database

Routine data is stored in PostgreSQL. The database has two tables:

- `events`: replaces the former `events.csv` data.
- `tasks`: replaces the former `todos.csv` data.

Docker Compose stores PostgreSQL data in the named volume `memory_assistant_db`. The initial schema and seed data are defined in `database/init/001_schema_and_seed.sql`. The caregiver page updates PostgreSQL only. It does not update the S3 documents or sync the Bedrock Knowledge Base.

## How The App Works

The user opens the frontend page in the browser. The main assistant page shows a question box, a voice input button, today's schedule, and open tasks.

When the user sends a memory question, the frontend calls the backend API. The Flask backend uses `boto3` to invoke the Amazon Bedrock Agent and returns the answer to the frontend.

Routine data is separate from the RAG documents. Events and tasks are read from PostgreSQL. The caregiver page can add events and tasks, and the monthly schedule page can show or remove events.

## Architecture

- `frontend`: Nginx container. Serves `frontend/index.html`, `frontend/static/styles.css`, `frontend/static/app.js`, `frontend/static/speech.js`, and the hero image.
- `backend`: Flask/Gunicorn container. Exposes private port `5000` inside the Docker network and handles Bedrock and routine API routes.
- `database`: PostgreSQL container. Stores events and tasks in a named Docker volume.
- Browser requests go to the frontend container.
- Frontend calls `/api/...`.
- Nginx proxies `/api/...` to `backend:5000`.
- Only the frontend publishes a host port.

## Run Locally

Create `.env` from the template:

```bash
cp .env.example .env
```

Fill in `.env` with your Bedrock values. If you are not using an EC2 IAM role or a local `~/.aws` profile, also set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. For local testing on a Mac, you can set `FRONTEND_PORT=8080` if port 80 is busy.

Start both containers:

```bash
docker compose up --build
```

Open the app with the configured frontend port:

```text
http://localhost
```

or, if `FRONTEND_PORT=8080`:

```text
http://localhost:8080
```

Stop the app:

```bash
docker compose down
```

Stop the app and delete the PostgreSQL data volume:

```bash
docker compose down -v
```

## EC2 Deployment Notes

AWS credential options:

- Recommended: attach an IAM role to the EC2 instance with permission to call Bedrock Agent Runtime for the Knowledge Base.
- Alternative for a short class demo: put `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env` on EC2. Do not commit `.env` and do not bake access keys into Docker images.

Security group:

- Allow inbound HTTP on port `80`.
- You do not need to expose backend port `5000` publicly.

Typical EC2 flow:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu
```

After reconnecting to the instance, copy or pull the project files. Create `.env`:

```bash
cp .env.example .env
```

Set:

```env
FRONTEND_PORT=80
AWS_REGION=us-east-2
BEDROCK_AGENT_ID=your-bedrock-agent-id
BEDROCK_AGENT_ALIAS_ID=your-bedrock-agent-alias-id
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
```

Run:

```bash
docker compose up --build -d
```

Open:

```text
http://EC2_PUBLIC_IP
```


## Cleanup Note

After testing, delete temporary AWS resources to avoid costs:

- Terminate the EC2 instance used for testing: `3.144.148.97`.
- Delete temporary security groups if they were created only for this project.
