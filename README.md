# AI 자기소개서 초안 생성 시스템 실행 가이드

본 프로젝트는 사용자의 경험 데이터와 워크넷 직무 데이터를 RAG(Retrieval-Augmented Generation) 방식으로 결합하여 고품질 자기소개서 초안을 생성하는 시스템입니다.

## 1. 사전 준비
- **Python 3.10+** 및 **Node.js 18+**가 설치되어 있어야 합니다.
- **OpenAI API Key**와 **워크넷 OpenAPI Key**가 필요합니다.

## 2. 백엔드 설정 및 실행
1. `backend/.env` 파일을 열어 API 키를 입력합니다.
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   WORKNET_API_KEY=your_worknet_api_key_here
   CHROMA_DB_PATH=./chroma_db
   ```
2. 가상환경 활성화 및 실행:
   ```bash
   cd backend
   # Windows
   .\venv\Scripts\activate
   # 백엔드 서버 실행
   python -m app.main
   ```
   *서버는 기본적으로 `http://localhost:8000`에서 실행됩니다.*

## 3. 프론트엔드 설정 및 실행
1. 새로운 터미널을 열고 프론트엔드 폴더로 이동합니다.
   ```bash
   cd frontend
   # 패키지 설치 (이미 완료됨)
   # 개발 서버 실행
   npm run dev
   ```
   *프론트엔드는 기본적으로 `http://localhost:5173`에서 실행됩니다.*

## 4. 주요 기능 및 흐름
1. **경험 입력**: 자신의 기술 스택, 주요 프로젝트 경험 등을 상세히 입력합니다. (ChromaDB에 벡터화 저장)
2. **직무 분석**: 지원하려는 직종을 입력하면 워크넷 API를 통해 시장의 핵심 요구 역량을 분석합니다.
3. **초안 생성 및 편집**: RAG를 통해 가장 관련 높은 경험을 선별하여 STAR 구조의 초안을 생성합니다. 사용자는 하이라이트된 플레이스홀더(`[수치 입력]`)를 직접 채웁니다.
4. **품질 검증**: 직무 정렬도, 콘텐츠 보존율, 플레이스홀더 완성도를 실시간으로 측정합니다.
5. **다운로드**: 모든 품질 게이트를 통과하면 최종 DOCX 파일을 다운로드할 수 있습니다.

## 5. 기술 스택
- **Backend**: FastAPI, ChromaDB, LangChain, OpenAI GPT-4o-mini
- **Frontend**: React 18, TypeScript, Tailwind CSS, Zustand, Lucide-React
- **Tools**: Scikit-learn (TF-IDF), Python-docx (DOCX Export)
