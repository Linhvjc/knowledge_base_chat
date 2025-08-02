import gradio as gr
import httpx
import json
from typing import List, Tuple
import asyncio

# URL của API FastAPI đang chạy trong cùng một hệ thống
API_URL = "http://localhost:8000"


async def handle_chat_interaction(message: str, history: List[dict]):
    """
    Xử lý tương tác chat, hiển thị từng chữ một.
    """
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": ""})

    # Chúng ta không yield ở đây nữa, sẽ yield bên trong vòng lặp

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST", f"{API_URL}/chat", json={"question": message}
            ) as response:
                response.raise_for_status()

                # Vòng lặp ngoài: xử lý từng chunk nhận được từ API
                async for chunk in response.aiter_text():
                    if not chunk:
                        continue

                    # Vòng lặp trong: xử lý từng ký tự trong chunk
                    for char in chunk:
                        history[-1]["content"] += char
                        # Thêm một khoảng nghỉ rất nhỏ để tạo hiệu ứng gõ phím mượt mà
                        # và cho phép trình duyệt có thời gian render.
                        await asyncio.sleep(0.005)
                        yield history  # Cập nhật UI sau mỗi ký tự

    except Exception as e:
        history[-1]["content"] = f"Lỗi: {str(e)}"
        yield history


async def handle_file_upload(file):
    """
    Xử lý việc tải file lên, đọc nội dung và gọi API /knowledge/update.
    """
    if not file:
        return "Vui lòng tải lên một file."

    with open(file.name, "r", encoding="utf-8") as f:
        content = f.read()

    payload = {"documents": [{"content": content, "metadata": {"source": file.name}}]}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{API_URL}/knowledge/update", json=payload)

    if response.status_code == 201:
        return f"Tải file '{file.name}' lên thành công!"
    else:
        return f"Lỗi: {response.status_code} - {response.text}"


async def get_knowledge_list():
    """
    Lấy danh sách các tài liệu hiện có và hiển thị chúng.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/knowledge")

    if response.status_code == 200:
        docs = response.json()
        if not docs:
            return "Chưa có tài liệu nào trong cơ sở tri thức."

        # Format thành Markdown để hiển thị
        markdown_output = (
            "| ID | Kích thước (bytes) | Metadata Nguồn |\n|---|---|---|\n"
        )
        for doc in docs:
            source = doc.get("doc_metadata", {}).get("source", "N/A")
            markdown_output += f"| `{doc['id']}` | {doc['size']} | {source} |\n"
        return markdown_output
    else:
        return f"Lỗi khi lấy danh sách tài liệu: {response.text}"


def create_ui():
    """
    Hàm chính tạo toàn bộ giao diện Gradio.
    """
    with gr.Blocks(theme=gr.themes.Soft(), title="Knowledge Base Chat") as demo:
        gr.Markdown("# Giao diện Demo cho Hệ thống Hỏi-Đáp")

        with gr.Tabs():
            with gr.TabItem("Chatbot"):
                chatbot = gr.Chatbot(
                    label="Cuộc hội thoại",
                    height=600,
                    bubble_full_width=False,
                    # Thêm dòng này để chuyển sang định dạng mới
                    type="messages",
                )
                msg = gr.Textbox(label="Nhập câu hỏi của bạn ở đây")
                clear = gr.ClearButton([msg, chatbot])
                msg.submit(handle_chat_interaction, [msg, chatbot], chatbot)

            with gr.TabItem("Quản lý Tri thức"):
                gr.Markdown("## Tải tài liệu mới")
                file_input = gr.File(label="Tải lên file .txt", file_types=[".txt"])
                upload_button = gr.Button("Tải lên")
                upload_status = gr.Textbox(
                    label="Trạng thái tải lên", interactive=False
                )

                upload_button.click(
                    handle_file_upload, inputs=file_input, outputs=upload_status
                )

                gr.Markdown("---")
                gr.Markdown("## Danh sách tài liệu hiện có")
                refresh_button = gr.Button("Làm mới danh sách")
                knowledge_display = gr.Markdown()

                refresh_button.click(get_knowledge_list, outputs=knowledge_display)

    return demo
