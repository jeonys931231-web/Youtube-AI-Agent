import os
import glob
import yt_dlp
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# ==========================================
# 1. API 및 환경 세팅
# ==========================================
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

st.set_page_config(page_title="갓생 엔진: 영상 분석기", page_icon="🚀", layout="centered")

st.title("🚀 갓생 엔진: 유튜브 심층 분석기")
st.markdown("""
Gemini 1.5의 강력한 멀티모달 기능을 활용하여 영상의 오디오를 직접 듣고 분석합니다. 
링크 하나면 핵심 내용과 기획/마케팅 인사이트를 즉시 뽑아드립니다.
""")

# ==========================================
# 2. 백엔드 함수들
# ==========================================
def get_youtube_data(youtube_url, output_filename="temp_audio"):
    """유튜브에서 제목, 설명, 오디오 파일 추출"""
    for file in glob.glob(f"{output_filename}.*"):
        os.remove(file)
        
    ydl_opts = {
        'format': 'm4a/bestaudio/best', 
        'outtmpl': f'{output_filename}.%(ext)s', 
        'quiet': True, 
        'extract_flat': False,
        'noplaylist': True,
        # ✨ 추가/수정된 우회 옵션들
        'source_address': '0.0.0.0', # 클라우드 서버의 IPv6 주소 차단 회피 (IPv4 강제 사용)
        'extractor_args': {'youtube': {'client': ['ios', 'tv', 'web']}} # 방어가 심한 안드로이드 대신 iOS와 스마트TV로 위장
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        title = info.get('title', '제목 없음')
        description = info.get('description', '설명 없음')
    
    audio_path = glob.glob(f"{output_filename}.*")[0]
    return title, description, audio_path

def analyze_video_with_gemini(title, description, audio_file_path):
    """Gemini API에 오디오 파일과 텍스트를 함께 보내 분석"""
    
    # 1. 로컬의 오디오 파일을 Gemini 서버로 업로드
    uploaded_audio = genai.upload_file(path=audio_file_path)
    
    # 2. 빠르고 강력한 Gemini 1.5 Flash 모델 선택
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 3. 실무 관점의 분석 프롬프트 작성
    prompt = f"""
    다음은 유튜브 영상의 정보와 업로드된 오디오 파일입니다. 오디오 내용을 직접 파악하고 영상을 종합적으로 분석하여 보고서를 작성해 주세요.

    [영상 제목]: {title}
    [영상 설명란]: {description}

    위 내용을 바탕으로 아래 양식에 맞춰 정리해 줘:
    1. 📝 영상 한 줄 요약: (가장 핵심적인 내용 한 줄)
    2. 🎯 주요 내용 요약: (3~5개의 불릿 포인트로 상세히)
    3. 💡 마케팅/콘텐츠 기획 인사이트: (뷰티/브랜드 마케팅 전략이나 채널 콘텐츠 기획에 적용할 만한 실무적인 아이디어와 배울 점)
    """
    
    # 4. 프롬프트와 오디오 파일을 함께 전달하여 결과 생성
    response = model.generate_content([prompt, uploaded_audio])
    
    # 5. 클라우드 공간 확보를 위해 업로드했던 파일 삭제
    uploaded_audio.delete()
    
    return response.text

# ==========================================
# 3. 프론트엔드 UI 및 실행 로직
# ==========================================
youtube_link = st.text_input("🔗 분석할 유튜브 링크를 입력하세요:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("분석 시작하기"):
    if youtube_link:
        try:
            with st.spinner('영상의 제목과 오디오를 추출하고 있습니다... 🎧'):
                video_title, video_desc, audio_file = get_youtube_data(youtube_link)
            
            st.success(f"✅ 대상 영상: {video_title}")
            
            with st.spinner('Gemini가 오디오를 직접 들으며 뷰티 마케팅 및 콘텐츠 기획 관점으로 심층 분석 중입니다... 🧠✨'):
                final_report = analyze_video_with_gemini(video_title, video_desc, audio_file)
            
            st.markdown("---")
            st.subheader("✨ [심층 분석 보고서]")
            st.markdown(final_report)
            
            if os.path.exists(audio_file):
                os.remove(audio_file)
                
        except Exception as e:
            st.error(f"❌ 에러가 발생했습니다: {e}")
            if 'audio_file' in locals() and os.path.exists(audio_file):
                os.remove(audio_file)
    else:
        st.warning("유튜브 링크를 먼저 입력해 주세요!")
