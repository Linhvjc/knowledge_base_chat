import gradio as gr
import httpx
import json
from typing import List, Tuple
import asyncio

# URL của API FastAPI đang chạy trong cùng một hệ thống
API_URL = "http://localhost:8000"


async def handle_chat_interaction(message: str, history_tuples: List[Tuple[str, str]]):
    """
    Xử lý tương tác chat multi-turn, chuyển đổi định dạng dữ liệu,
    VÀ stream từng ký tự.

    Args:
        message (str): Tin nhắn mới từ người dùng.
        history_tuples (List[Tuple[str, str]]): Lịch sử ở định dạng Gradio.
    """
    # 1. Chuyển đổi history từ định dạng của Gradio sang định dạng backend cần.
    history_for_api = []
    for user_msg, assistant_msg in history_tuples:
        history_for_api.append({"role": "user", "content": user_msg})
        history_for_api.append({"role": "assistant", "content": assistant_msg})

    # 2. Chuẩn bị payload để gửi đến backend.
    payload = {"question": message, "history": history_for_api}

    # 3. Cập nhật UI ngay lập tức với câu hỏi của người dùng và
    #    một placeholder cho câu trả lời của bot.
    history_tuples.append([message, ""])

    # Bắt đầu stream và điền vào placeholder đó
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST", f"{API_URL}/chat", json=payload
            ) as response:
                response.raise_for_status()

                # === PHẦN SỬA LỖI STREAMING NẰM Ở ĐÂY ===
                # Lặp qua từng chunk
                async for chunk in response.aiter_text():
                    if not chunk:
                        continue
                    # Lặp qua từng ký tự trong chunk
                    for char in chunk:
                        # Cập nhật tin nhắn của bot với từng ký tự
                        history_tuples[-1][1] += char
                        # Thêm độ trễ nhỏ để tạo hiệu ứng mượt mà
                        await asyncio.sleep(0.005)
                        # Yield để cập nhật UI sau MỖI KÝ TỰ
                        yield history_tuples

    except Exception as e:
        history_tuples[-1][1] = f"Đã xảy ra lỗi: {str(e)}"
        yield history_tuples


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


async def handle_delete_knowledge(doc_id: str):
    """
    Xử lý việc xóa một tài liệu bằng ID và gọi API DELETE.
    """
    if not doc_id or not doc_id.strip():
        return "Vui lòng nhập một Document ID."

    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{API_URL}/knowledge/{doc_id.strip()}")

        if response.status_code == 200:
            return f"Xóa thành công document ID: {doc_id}"
        elif response.status_code == 404:
            return f"Lỗi: Không tìm thấy document với ID: {doc_id}"
        else:
            return f"Lỗi từ server: {response.status_code} - {response.text}"

    except Exception as e:
        return f"Đã xảy ra lỗi không mong muốn: {str(e)}"


async def handle_delete_all_knowledge():
    """
    Xử lý việc xóa tất cả tài liệu bằng cách gọi API.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{API_URL}/knowledge/all")

        if response.status_code == 200:
            detail = response.json().get("detail", "Đã xóa tất cả tài liệu.")
            return f"Thành công: {detail}"
        else:
            return f"Lỗi từ server: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Đã xảy ra lỗi không mong muốn: {str(e)}"


def create_ui():
    """
    Hàm chính tạo toàn bộ giao diện Gradio với đầy đủ chức năng.
    """
    with gr.Blocks(theme=gr.themes.Soft(), title="Knowledge Base Chat") as demo:
        gr.Markdown("# Giao diện Demo cho Hệ thống Hỏi-Đáp")

        with gr.Tabs():
            with gr.TabItem("Chatbot"):
                chatbot = gr.Chatbot(
                    label="Cuộc hội thoại", height=600, bubble_full_width=False
                )
                msg = gr.Textbox(label="Nhập câu hỏi của bạn ở đây")
                clear = gr.ClearButton([msg, chatbot])

                # Chuỗi sự kiện hoàn chỉnh cho việc chat
                msg.submit(handle_chat_interaction, [msg, chatbot], chatbot).then(
                    lambda: gr.update(value=""), None, outputs=msg, queue=False
                )

            with gr.TabItem("Quản lý Tri thức"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("## Tải tài liệu mới")
                        file_input = gr.File(
                            label="Tải lên file .txt", file_types=[".txt"]
                        )
                        upload_button = gr.Button("Tải lên")
                        upload_status = gr.Textbox(
                            label="Trạng thái tải lên", interactive=False
                        )

                        upload_button.click(
                            handle_file_upload, inputs=file_input, outputs=upload_status
                        )

                        gr.Markdown("---")
                        gr.Markdown("## Xóa tài liệu")
                        doc_id_to_delete = gr.Textbox(label="Nhập Document ID cần xóa")
                        delete_button = gr.Button("Xóa Document")
                        delete_status = gr.Textbox(
                            label="Trạng thái xóa", interactive=False
                        )

                        # --- THÊM CÁC COMPONENT MỚI Ở ĐÂY ---
                        gr.Markdown("### Hành động nguy hiểm")
                        delete_all_button = gr.Button(
                            "Xóa TẤT CẢ Tri thức", variant="stop"
                        )
                        delete_all_status = gr.Textbox(
                            label="Trạng thái xóa tất cả", interactive=False
                        )
                        # ------------------------------------

                    with gr.Column(scale=2):
                        gr.Markdown("## Danh sách tài liệu hiện có")
                        refresh_button = gr.Button("Làm mới danh sách")
                        knowledge_display = gr.Markdown()

                # --- CẬP NHẬT CÁC SỰ KIỆN ---
                refresh_button.click(get_knowledge_list, outputs=knowledge_display)

                delete_button.click(
                    handle_delete_knowledge,
                    inputs=doc_id_to_delete,
                    outputs=delete_status,
                ).then(get_knowledge_list, None, outputs=knowledge_display)

                # Thêm sự kiện cho nút xóa tất cả
                delete_all_button.click(
                    handle_delete_all_knowledge,
                    inputs=None,  # Không cần input
                    outputs=delete_all_status,
                ).then(  # Sau khi xóa xong, cũng tự động làm mới danh sách
                    get_knowledge_list, None, outputs=knowledge_display
                )

    return demo
