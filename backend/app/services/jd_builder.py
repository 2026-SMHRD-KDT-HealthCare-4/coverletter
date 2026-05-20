import os
import requests
import xmltodict
from sklearn.feature_extraction.text import TfidfVectorizer
from app.models.schemas import JDKeyword, JDContext
from typing import List
import re

class JDContextBuilder:
    def __init__(self):
        self.worknet_key = os.getenv("WORKNET_API_KEY")
        self.wanted_api_url = "http://openapi.work.go.kr/opi/opi/opia/wantedApi.do"
        # Using a representative NCS-like structure or another Worknet endpoint if available
        # For this prototype, we'll focus on the Wanted API and mock the dictionary if needed
        self.job_dict_api_url = "http://openapi.work.go.kr/opi/opi/opia/jobDictApi.do" 

    def fetch_recruitment_data(self, job_keyword: str, count: int = 20):
        params = {
            "authKey": self.worknet_key,
            "callTp": "L",
            "returnType": "XML",
            "startPage": 1,
            "display": count,
            "keyword": job_keyword
        }
        try:
            response = requests.get(self.wanted_api_url, params=params)
            data = xmltodict.parse(response.text)
            wanted_data = data.get("wantedRoot", {}).get("wanted", [])
            
            # If only one result is returned, xmltodict returns a dict instead of a list
            if isinstance(wanted_data, dict):
                return [wanted_data]
            return wanted_data
        except Exception as e:
            print(f"Error fetching recruitment data: {e}")
            return []

    def extract_keywords(self, job_descriptions: List[str]):
        if not job_descriptions or len(job_descriptions) < 2:
            return [JDKeyword(keyword="데이터 부족", frequency=0.0)]
        
        # Enhanced tokenizer for Korean and English technical terms
        # Extracts words with 2 or more characters including Korean, English, and numbers
        token_pattern = r"[ㄱ-ㅎㅏ-ㅣ가-힣a-zA-Z0-9]{2,}"
        
        vectorizer = TfidfVectorizer(
            max_features=15,
            token_pattern=token_pattern,
            stop_words=['경험자', '우대사항', '경력직', '모십니다', '신입사원'] # Simple stop words
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(job_descriptions)
            feature_names = vectorizer.get_feature_names_out()
            
            scores = tfidf_matrix.mean(axis=0).tolist()[0]
            keywords = []
            for name, score in zip(feature_names, scores):
                # Filter out very low score generic words
                if score > 0.01:
                    keywords.append(JDKeyword(keyword=name, frequency=score))
            
            keywords.sort(key=lambda x: x.frequency, reverse=True)
            return keywords if keywords else [JDKeyword(keyword="키워드 없음", frequency=0.0)]
        except:
            return [JDKeyword(keyword="분석 오류", frequency=0.0)]

    def clean_text(self, text: str):
        if not text:
            return ""
        text = re.sub(r'<[^>]*>', '', text)
        # Keep Korean, English, and Numbers
        text = re.sub(r'[^ㄱ-ㅎㅏ-ㅣ가-힣a-zA-Z0-9\s]', '', text)
        return text

    async def build_context(self, job_name: str) -> JDContext:
        raw_wanted = self.fetch_recruitment_data(job_name)
        
        job_descs = []
        for item in raw_wanted:
            # Focus on titles as they often contain key technologies
            title = item.get("wantedTitle", "")
            # jobsNm often contains detailed job categories
            job_category = item.get("jobsNm", "")
            
            # Combine meaningful fields for analysis
            desc_text = f"{title} {job_category}"
            cleaned = self.clean_text(desc_text)
            if cleaned:
                job_descs.append(cleaned)
            
        keywords = self.extract_keywords(job_descs)
        
        # Build the final context string
        context_str = f"직종: {job_name}\n\n"
        context_str += "시장 주요 요구 사항(추출 키워드):\n"
        context_str += ", ".join([kw.keyword for kw in keywords]) + "\n\n"
        
        context_str += "표준 직무 역량(NCS 기반):\n- 사용자 요구사항 분석 및 화면 설계\n- 컴포넌트 구조화 및 상태 관리 설계\n- UI 가이드라인 준수 및 디자인 시스템 적용"
        
        return JDContext(
            job_name=job_name,
            context=context_str,
            keywords=keywords
        )
