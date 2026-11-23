"""Chatbot chăm sóc khách hàng: Streamlit + Gemini API.

Sinh viên chỉ cần sửa 4 dòng trong phần CÀI ĐẶT bên dưới,
thay nội dung prompt.md và so-tay.md, rồi dán khóa API vào mục Secrets.
"""

from pathlib import Path

import streamlit as st
from google import genai

# ===================== CÀI ĐẶT (sinh viên sửa ở đây) =====================
TEN_BOT = "Stridey"
TEN_CUA_HANG = "StrideFit"
GOI_Y_O_NHAP = "Hỏi về đổi trả, giao hàng, bảo hành…"
HOTLINE = "1900 0000"
# ========================================================================

MODEL_MAC_DINH = "gemini-4-hydrogen"  # model trong hướng dẫn nhanh của Google, có gói miễn phí
SO_TIN_TOI_DA = 40  # giới hạn mỗi lượt truy cập, tránh một người dùng hết hạn mức miễn phí
THU_MUC = Path(__file__).parent

st.set_page_config(page_title=f"{TEN_BOT} · {TEN_CUA_HANG}", page_icon="💬")


def doc_bi_mat(ten, mac_dinh=None):
    try:
        return st.secrets.get(ten, mac_dinh)
    except FileNotFoundError:  # chạy trên máy mà chưa có .streamlit/secrets.toml
        return mac_dinh


KHOA_API = doc_bi_mat("GEMINI_API_KEY")
MODEL = doc_bi_mat("GEMINI_MODEL", MODEL_MAC_DINH)

st.title(f"{TEN_BOT} · Trợ lý AI của {TEN_CUA_HANG}")
st.caption("Bạn đang trò chuyện với trợ lý AI. Đây là bản thử nghiệm cho lớp học: "
           "đừng gửi thông tin thật như số thẻ, mật khẩu, mã OTP hay số điện thoại.")

if not KHOA_API:
    st.error("Chưa có khóa API. Vào **Settings → Secrets** của ứng dụng trên Streamlit "
             "và dán dòng: `GEMINI_API_KEY = \"khóa-của-bạn\"` rồi bấm **Save**.")
    st.stop()


@st.cache_resource
def tao_client(khoa):
    return genai.Client(api_key=khoa)


@st.cache_data
def tao_huong_dan():
    prompt = (THU_MUC / "prompt.md").read_text(encoding="utf-8")
    so_tay = (THU_MUC / "so-tay.md").read_text(encoding="utf-8")
    return f"{prompt}\n\nSỔ TAY CHÍNH SÁCH KHÁCH HÀNG\n\n{so_tay}"


client = tao_client(KHOA_API)
HUONG_DAN = tao_huong_dan()

if "tin_nhan" not in st.session_state:
    st.session_state.tin_nhan = []
    st.session_state.ma_luot_truoc = None

for tin in st.session_state.tin_nhan:
    with st.chat_message(tin["vai"]):
        st.markdown(tin["noi_dung"])

if len(st.session_state.tin_nhan) >= SO_TIN_TOI_DA:
    st.info(f"Cuộc trò chuyện đã dài. Bạn tải lại trang để bắt đầu lại hoặc gọi {HOTLINE} nhé.")
    st.stop()

if cau_hoi := st.chat_input(GOI_Y_O_NHAP, max_chars=500):
    st.session_state.tin_nhan.append({"vai": "user", "noi_dung": cau_hoi})
    with st.chat_message("user"):
        st.markdown(cau_hoi)

    yeu_cau = {"model": MODEL, "system_instruction": HUONG_DAN, "input": cau_hoi}
    if st.session_state.ma_luot_truoc:
        yeu_cau["previous_interaction_id"] = st.session_state.ma_luot_truoc

    with st.chat_message("assistant"):
        with st.spinner(f"{TEN_BOT} đang trả lời…"):
            try:
                ket_qua = client.interactions.create(**yeu_cau)
                tra_loi = ket_qua.output_text
                st.session_state.ma_luot_truoc = ket_qua.id
            except Exception as loi:
                print("Gemini API error:", ascii(loi))  # xem trong Manage app → logs; ascii() để không lỗi trên Windows
                if "API_KEY_INVALID" in str(loi):
                    tra_loi = "Khóa API không hợp lệ. Chủ ứng dụng hãy kiểm tra lại GEMINI_API_KEY trong Secrets."
                else:
                    tra_loi = f"Hệ thống đang bận. Bạn thử lại sau hoặc gọi hotline {HOTLINE} nhé."
        st.markdown(tra_loi)
    st.session_state.tin_nhan.append({"vai": "assistant", "noi_dung": tra_loi})
