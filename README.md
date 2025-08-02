# Interview Project: Knowledge Base AI System

Đây là một hệ thống Hỏi-Đáp (Q&A) được xây dựng dựa trên kiến trúc RAG (Retrieval-Augmented Generation). Hệ thống cho phép người dùng tải lên tài liệu, đặt câu hỏi dựa trên các tài liệu đó, và nhận được câu trả lời từ AI.

## Mục tiêu

Thiết kế một hệ thống knowledge base được container hóa sử dụng FastAPI, PostgreSQL (với pgvector), LangChain/LangGraph, và Gemini. Hệ thống hỗ trợ CRUD đầy đủ trên dữ liệu vector, trả về API streaming, và ghi lại nhật ký cho mỗi tương tác.

## Tech Stack

*   **Framework:** FastAPI
*   **Database:** PostgreSQL + pgvector extension
*   **Orchestration:** Docker & Docker Compose
*   **AI/LLM:** Google Gemini
*   **Core Logic:** LangChain & LangGraph
*   **Database ORM:** SQLAlchemy (Async)

## Yêu cầu

*   Docker
*   Docker Compose

## Hướng dẫn Cài đặt và Chạy

1.  **Clone a repository:**
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Tạo file biến môi trường:**
    Sao chép file `.env.example` thành `.env` và điền `GEMINI_API_KEY` của bạn vào.
    ```bash
    cp .env.example .env
    ```
    Sau đó mở file `.env` và chỉnh sửa:
    ```
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
    ```

3.  **Chạy hệ thống bằng Docker Compose:**
    Lệnh này sẽ build image cho API, kéo image PostgreSQL, và khởi động cả hai container.
    ```bash
    docker-compose up --build
    ```
    Hệ thống API sẽ có thể truy cập tại `http://localhost:8000`.

## API Endpoints

Bạn có thể xem tài liệu API tự động tại `http://localhost:8000/docs`.

Dưới đây là các ví dụ sử dụng `cURL`:

#### 1. Thêm tài liệu vào Knowledge Base

*   **Endpoint:** `POST /knowledge/update`
*   **cURL:**
    ```bash
    curl -X 'POST' \
      'http://localhost:8000/knowledge/update' \
      -H 'Content-Type: application/json' \
      -d '{
        "documents": [
          {
            "content": "LangChain là một framework để phát triển các ứng dụng được cung cấp bởi các mô hình ngôn ngữ.",
            "metadata": {"source": "langchain_docs.txt"}
          }
        ]
      }'
    ```

#### 2. Chat với Knowledge Base (Streaming)

*   **Endpoint:** `POST /chat`
*   **cURL:** (Tùy chọn `-N` để xem stream)
    ```bash
    curl -N -X 'POST' \
      'http://localhost:8000/chat' \
      -H 'Content-Type: application/json' \
      -d '{"question": "LangChain là gì?"}'
    ```

#### 3. Lấy danh sách các tài liệu

*   **Endpoint:** `GET /knowledge`
*   **cURL:**
    ```bash
    curl -X 'GET' 'http://localhost:8000/knowledge'
    ```

#### 4. Lấy chi tiết một cuộc hội thoại

*   **Endpoint:** `GET /audit/{chat_id}`
*   **cURL:** (Thay thế `chat_id` bạn nhận được từ log sau khi chat)
    ```bash
    curl -X 'GET' 'http://localhost:8000/audit/your-chat-id-here'
    ```

#### 5. Xóa một tài liệu

*   **Endpoint:** `DELETE /knowledge/{doc_id}`
*   **cURL:** (Thay thế `doc_id` bạn nhận được từ `GET /knowledge`)
    ```bash
    curl -X 'DELETE' 'http://localhost:8000/knowledge/your-doc-id-here'
    ```