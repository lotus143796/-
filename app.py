import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from agent.core import CodeReviewAgent

load_dotenv()

st.set_page_config(page_title="Code Review Agent", layout="wide")
st.title("🤖 智能代码审查 Agent - 支持多语言 & 整个文件夹")

api_key = st.sidebar.text_input("DeepSeek API Key", type="password", value=os.getenv("DEEPSEEK_API_KEY", ""))
model = st.sidebar.selectbox("模型", ["deepseek-chat", "deepseek-coder"])
max_steps = st.sidebar.slider("Agent 最大步数", 3, 10, 5)

mode = st.radio("审查模式", ["单个文件", "整个文件夹"])

code = ""
file_path = None
folder_path = None

if mode == "单个文件":
    uploaded = st.file_uploader("上传代码文件", type=["py","java","js","go","rs","cpp","c"])
    if uploaded:
        code = uploaded.read().decode("utf-8")
        file_path = uploaded.name
        st.code(code, language=file_path.split('.')[-1])
else:
    uploaded_folder = st.file_uploader("上传文件夹（压缩包）或输入路径", type=["zip"])
    folder_input = st.text_input("或输入文件夹绝对路径")
    if uploaded_folder:
        # 解压 zip
        import zipfile
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "upload.zip")
            with open(zip_path, "wb") as f:
                f.write(uploaded_folder.getbuffer())
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmpdir)
            folder_path = tmpdir
            st.success(f"已解压到临时目录，共 {len(os.listdir(tmpdir))} 个文件")
    elif folder_input and os.path.isdir(folder_input):
        folder_path = folder_input
        st.success(f"使用文件夹: {folder_path}")

if st.button("开始审查", type="primary"):
    if not api_key:
        st.error("请填写 API Key")
    else:
        agent = CodeReviewAgent(api_key=api_key, model=model, max_steps=max_steps)
        if mode == "单个文件" and code:
            with st.spinner("Agent 分析中..."):
                result = agent.run(code, file_path)
            st.subheader("审查报告")
            st.json(result.get("report", {}))
            with st.expander("Agent 思考过程"):
                st.text(agent.visualize_steps())
        elif mode == "整个文件夹" and folder_path:
            with st.spinner("正在扫描并分析整个项目..."):
                result = agent.run_on_project(folder_path)
            st.subheader("项目汇总报告")
            st.write(f"**{result['summary']}**")
            st.json(result.get("project_analysis", {}))
            st.write(f"**问题列表** (共 {len(result.get('issues', []))} 个)")
            for issue in result.get('issues', [])[:20]:
                st.markdown(f"- `{issue.get('file')}` : {issue.get('description')}")
        else:
            st.warning("请提供代码或文件夹")