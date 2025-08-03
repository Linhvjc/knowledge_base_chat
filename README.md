# Interactive RAG Knowledge Base AI System

This project is a comprehensive Question & Answering (Q&A) system built on a Retrieval-Augmented Generation (RAG) architecture. It allows users to ingest documents, ask context-aware questions based on that knowledge, and receive intelligent, conversational answers from an AI.

The entire system is containerized using Docker and features an intuitive web interface built with Gradio for easy interaction and demonstration.

## UI Demo

Once launched, the interactive web interface is available at: **[http://localhost:8000/ui](http://localhost:8000/ui)**

**[DEMO VIDEO](https://drive.google.com/file/d/1are_FDtHUfu7EGv8wZOnNfAvYxDjsOtu/view?usp=sharing)**

## Key Features

*   **Complete RAG System:** Integrates a Retrieval flow from a vector database and a Generation flow from an LLM.
*   **Multi-Turn Conversations:** The chatbot maintains conversational context, allowing for follow-up questions.
*   **Streaming Responses:** AI-generated answers are streamed token-by-token, creating a real-time "typewriter" effect for an enhanced user experience.
*   **Knowledge Management (CRUD):**
    *   **Create:** Upload `.txt` documents to add them to the knowledge base.
    *   **Read:** List all ingested document chunks.
    *   **Delete:** Remove a specific document chunk by its ID.
*   **Audit Logging:** Every chat interaction is logged to the database, including the question, response, retrieved context, and latency.
*   **Robust API Backend:** Built with FastAPI, providing a full suite of endpoints for management and interaction.
*   **Fully Containerized:** The entire system (API, Database) is orchestrated with Docker and Docker Compose, enabling a one-command setup.
*   **Intuitive Web UI:** A user-friendly interface built with Gradio allows for easy demonstration and interaction with all core features.

## Tech Stack

*   **Application Framework:** FastAPI
*   **UI Framework:** Gradio
*   **Database:** PostgreSQL
*   **Vector Search:** `pgvector` (PostgreSQL extension)
*   **Core AI Logic:** LangChain, LangGraph
*   **Language Model (LLM):** Google Gemini (`gemini-2.0-flash-exp`)
*   **Embedding Model:** Google `embedding-001`
*   **Database ORM:** SQLAlchemy (Async)
*   **Containerization:** Docker & Docker Compose

## How It Works

1.  **Knowledge Ingestion (`/knowledge/update`):**
    *   Text from an uploaded document is split into smaller `chunks`.
    *   Each `chunk` is converted into a numerical `vector` using the embedding model.
    *   The `(chunk, vector)` pair is stored in the PostgreSQL database (using pgvector).

2.  **Chat Interaction (`/chat`):**
    *   The user's question is converted into a query `vector`.
    *   The system performs a similarity search in `pgvector` to find the text `chunks` most relevant to the question. This becomes the **Context**.
    *   **LangGraph** orchestrates the flow:
        1.  **`retrieve` Node**: Executes the context search.
        2.  **`generate` Node**: Sends the **Conversation History**, the retrieved **Context**, and the new **Question** to the Gemini LLM to generate a final, informed answer.
    *   The response is streamed back to the UI.
    *   The entire session is saved to the `audit_logs` table.

## System Requirements

*   Git
*   Docker
*   Docker Compose

## Setup and Run Instructions

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Linhvjc/knowledge_base_chat.git
    cd knowledge_base_chat
    ```

2.  **Create Environment File:**
    Copy the example `.env.example` file to a new file named `.env`.
    ```bash
    cp .env.example .env
    ```
    Then, open the `.env` file and add your `GEMINI_API_KEY`:
    ```dotenv
    # PostgreSQL Database URL
    # Format: postgresql+asyncpg://<user>:<password>@<host>:<port>/<dbname>
    DATABASE_URL=postgresql+asyncpg://user:password@db:5432/knowledge_base_db

    # API URL
    API_URL="http://localhost:8000"

    # Models
    EMBEDDING_MODEL="models/embedding-001"
    LLM_MODEL="gemini-2.0-flash-exp"

    # Google Gemini API Key
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
    ```

3.  **Launch the System:**
    Use Docker Compose to build the images and run all services.
    ```bash
    docker-compose up --build
    ```
    Wait a moment for Docker to pull the necessary images and start the containers. Once complete, the system is ready!

4.  **Access and Test:**
    *   **User Interface:** Open your browser and navigate to **`http://localhost:8000/ui`**
    *   **API Documentation:** `http://localhost:8000/docs` (Auto-generated Swagger UI)

## UI Usage Guide

#### 1. Adding Knowledge
*   Navigate to `http://localhost:8000/ui` and select the **"Knowledge Management"** tab.
*   Under "Upload New Document", select a `.txt` file from your computer.
*   Click the **"Upload"** button. The status will be displayed.
*   Click the **"Refresh List"** button on the right column to see the newly added document.

#### 2. Chatting with the AI
*   Switch to the **"Chatbot"** tab.
*   Enter a question related to the content of your uploaded documents.
*   Press Enter and watch the response being generated.

#### 3. Deleting Knowledge
*   In the **"Knowledge Management"** tab, click **"Refresh List"** to view the IDs of the documents.
*   Copy an `ID` from the list.
*   Paste it into the "Enter Document ID to delete" field.
*   Click the **"Delete Document"** button. The list will automatically update.

## API Endpoints (For Advanced Testing)

You can use `cURL` or tools like Postman to interact with the API directly.

#### 1. Add Documents to Knowledge Base
*   **Endpoint:** `POST /knowledge/update`
*   **cURL:**
    ```bash
    curl -X 'POST' \
      'http://localhost:8000/knowledge/update' \
      -H 'Content-Type: application/json' \
      -d '{
        "documents": [
          {
            "content": "LangChain is a framework for developing applications powered by language models.",
            "metadata": {"source": "langchain_docs.txt"}
          }
        ]
      }'
    ```

#### 2. Get List of Documents
*   **Endpoint:** `GET /knowledge`
*   **cURL:**
    ```bash
    curl -X 'GET' 'http://localhost:8000/knowledge'
    ```

#### 3. Chat with Knowledge Base (Streaming)
*   **Endpoint:** `POST /chat`
*   **cURL:** (The `-N` flag is for no-buffering to see the stream immediately)
    ```bash
    curl -N -X 'POST' \
      'http://localhost:8000/chat' \
      -H 'Content-Type: application/json' \
      -d '{"question": "What is LangChain?", "history": []}'
    ```

#### 4. Delete a Specific Document
*   **Endpoint:** `DELETE /knowledge/{id}`
*   **cURL:** (Replace `<YOUR_DOCUMENT_ID_HERE>` with an ID from `GET /knowledge`)
    ```bash
    curl -X 'DELETE' 'http://localhost:8000/knowledge/<YOUR_DOCUMENT_ID_HERE>'
    ```

#### 5. Get Chat Audit Details
*   **Endpoint:** `GET /audit/{chat_id}`
*   **cURL:** (Replace `<YOUR_CHAT_ID_HERE>` with an ID from the `api-1` container logs after a chat session)
    ```bash
    curl -X 'GET' 'http://localhost:8000/audit/<YOUR_CHAT_ID_HERE>'
    ```

## Architecture Choices

A detailed document explaining the rationale behind the technology choices (FastAPI, pgvector, LangGraph, etc.) can be found in [ARCHITECTURE.md](./ARCHITECTURE.md).

## Project Structure

```
/project
├── app/                      # Main application source code
│   ├── api/                  # API Endpoints (routers)
│   ├── core/                 # Core configuration
│   ├── db/                   # Database-related logic
│   ├── graph/                # LangGraph logic (RAG)
│   ├── schemas/              # Pydantic models (data validation)
│   ├── services/             # Business logic
│   ├── ui/                   # Gradio UI logic
│   └── main.py               # FastAPI application entrypoint
├── .env.example              # Environment variables template
├── .gitignore                # Files/folders to be ignored by Git
├── ARCHITECTURE.md           # Explanation of architecture decisions
├── docker-compose.yml        # Docker services definition
├── Dockerfile                # Recipe to build the FastAPI image
├── README.md                 # This documentation file
└── requirements.txt          # Python library dependencies
```
