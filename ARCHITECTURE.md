# Architecture Decisions

This document outlines the key architectural decisions made during the development of the RAG Knowledge Base AI System. Each choice was made to balance performance, scalability, development speed, and operational simplicity.

---

## 1. FastAPI

FastAPI was chosen as the core web framework for the backend API.

*   **Why FastAPI?**
    *   **High Performance:** Built on top of Starlette and Pydantic, FastAPI is one of the fastest Python web frameworks available, which is crucial for delivering low-latency API responses as required by the project constraints.
    *   **Asynchronous Support:** Its native `async`/`await` syntax is perfectly suited for AI applications, which are heavily I/O-bound. This allows the server to efficiently handle long-running operations like database queries and calls to the external Gemini LLM API without blocking, enabling high concurrency.
    *   **Integrated Data Validation:** Pydantic integration provides automatic request/response data validation, serialization, and documentation. This drastically reduces boilerplate code, minimizes runtime errors, and auto-generates interactive API documentation (Swagger UI), which accelerates both development and testing.

## 2. PostgreSQL + pgvector

Instead of using a separate, specialized vector database, we chose to use PostgreSQL with the `pgvector` extension.

*   **Why PostgreSQL + pgvector?**
    *   **Unified System:** This approach allows us to store both relational data (like the `audit_logs`) and high-dimensional vector data (the `embeddings`) within a single, robust database system. It eliminates the complexity of managing, backing up, and securing two different database technologies.
    *   **Simplified Deployment:** The architecture requires only one database service in the `docker-compose.yml` file, making the system easier to deploy, maintain, and scale.
    *   **Leverages PostgreSQL's Strengths:** We can utilize the full power of a mature RDBMS, including ACID transactions, robust indexing for metadata, and advanced query capabilities, alongside efficient vector similarity search. This is more powerful and flexible than a vector-only solution.

## 3. LangChain & LangGraph

The core AI logic was built using the LangChain ecosystem, specifically with LangGraph for orchestrating the RAG pipeline.

*   **Why LangChain?**
    *   **Abstractions and Modularity:** LangChain provides high-level abstractions for essential components like `TextSplitter`, `Embeddings`, and `ChatModels`. This abstracts away the complexity of direct API integrations and allows for easy swapping of components (e.g., changing the embedding model in the future would be a one-line change).

*   **Why LangGraph?**
    *   **Explicit State Management:** LangGraph allows us to define our RAG pipeline as a stateful graph. The `GraphState` object provides a clear, traceable path for data as it moves through the system, making debugging and understanding the flow much easier.
    *   **Transparency and Control:** The flow is defined as a clear, directed graph (`retrieve` -> `generate`). This is more transparent and controllable than a monolithic, "magical" chain.
    *   **Extensibility:** This architecture is highly extensible. It is trivial to add new nodes to the graph in the future, such as a node for checking context quality, a node for deciding whether to use a tool, or a self-correction loop. This makes the system robust and future-proof.

## 4. Docker & Docker Compose

The entire application is containerized and orchestrated using Docker and Docker Compose.

*   **Why Docker & Docker Compose?**
    *   **Environment Consistency:** Docker ensures that the application runs in an identical, isolated environment, regardless of the host machine. This eliminates the "it works on my machine" problem and guarantees that what is developed is what gets deployed.
    *   **One-Command Deployment:** A core project requirement was a "single command to launch the entire system." `docker-compose up` perfectly fulfills this, orchestrating the API service and the database service, including their networking and dependencies.
    *   **Microservice-Ready Architecture:** This setup establishes a foundation for a microservice architecture. Services can be scaled, updated, or replaced independently, promoting a modular and maintainable system design.

## 5. Gradio

A web UI was built using Gradio and mounted directly onto the FastAPI application.

*   **Why Gradio?**
    *   **Rapid Prototyping and Demo:** Gradio is designed to create intuitive UIs for machine learning applications with minimal code. This allowed for the rapid development of an interactive demo to showcase all backend functionalities.
    *   **Seamless Integration:** As a Python library, Gradio integrates seamlessly into the existing codebase. By mounting the Gradio app onto a FastAPI route (`gr.mount_gradio_app`), we serve both the API and the UI from a single process, simplifying the overall architecture and avoiding the need for a separate frontend project (e.g., React/Vue).

## System Data Flow

#### Knowledge Ingestion (`POST /knowledge/update`)

1.  The client sends a JSON payload containing a list of documents.
2.  The FastAPI endpoint receives and validates the payload using a Pydantic model.
3.  The `KnowledgeService` splits the text of each document into smaller `chunks`.
4.  The `GoogleGenerativeAIEmbeddings` model converts each `chunk` into a numerical vector.
5.  SQLAlchemy ORM performs a bulk `INSERT` of the `(content, embedding, metadata)` for each chunk into the `documents` table in PostgreSQL.

#### Chat Interaction (`POST /chat`)

1.  The Gradio UI sends the new question and the conversation history to the FastAPI `/chat` endpoint.
2.  The `ChatService` receives the request and initializes the `LangGraph` runnable.
3.  **`retrieve` Node:**
    *   The user's question is converted into a query vector.
    *   A similarity search query is executed against `pgvector` to find the most relevant document `chunks` (the context).
    *   The `context` and `retrieved_docs` are added to the graph's state.
4.  **`generate` Node:**
    *   A list of messages is constructed, including a system prompt, the previous `chat_history`, and a final prompt combining the new `question` and the retrieved `context`.
    *   This complete message list is sent to the Gemini model.
5.  **Streaming & Logging:**
    *   The `ChatService` streams the LLM's response back to the Gradio UI token-by-token.
    *   After the stream is complete, a detailed `AuditLog` entry (question, response, context, latency) is saved to the PostgreSQL database.
