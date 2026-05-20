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

    def fetch_job_dict_data(self, job_keyword: str):
        params = {
            "authKey": self.worknet_key,
            "returnType": "XML",
            "target": "JOBCD", # Job Dictionary target
            "srchKey": job_keyword
        }
        try:
            # Note: The actual endpoint might differ based on the specific Worknet API version
            # Here we assume a standard REST call to the Job Dictionary endpoint
            response = requests.get(self.job_dict_api_url, params=params)
            data = xmltodict.parse(response.text)
            dict_data = data.get("jobDictRoot", {}).get("jobDict", [])
            
            if isinstance(dict_data, dict):
                return [dict_data]
            return dict_data
        except Exception as e:
            print(f"Error fetching job dictionary data: {e}")
            return []

    async def build_context(self, job_name: str) -> JDContext:
        # 1. Fetch real-time recruitment data
        raw_wanted = self.fetch_recruitment_data(job_name)
        job_descs = []
        for item in raw_wanted:
            title = item.get("wantedTitle", "")
            job_category = item.get("jobsNm", "")
            desc_text = f"{title} {job_category}"
            cleaned = self.clean_text(desc_text)
            if cleaned:
                job_descs.append(cleaned)
            
        keywords = self.extract_keywords(job_descs)
        
        # 2. Fetch standard job dictionary data (NCS-based)
        raw_dict = self.fetch_job_dict_data(job_name)
        standard_competencies = []
        
        if raw_dict:
            # Extract main tasks or definitions from the dictionary
            for item in raw_dict[:3]: # Take top 3 related job definitions
                task = item.get("jobDefinition", "") or item.get("mainWork", "")
                if task:
                    cleaned_task = self.clean_text(task)
                    if cleaned_task:
                        standard_competencies.append(cleaned_task)
        
        # 3. Build the final dynamic context string
        context_str = f"직종: {job_name}\n\n"
        context_str += "시장 주요 요구 사항(추출 키워드):\n"
        context_str += ", ".join([kw.keyword for kw in keywords]) + "\n\n"
        
        context_str += "표준 직무 역량(Job Dictionary/NCS 기반):\n"
        if standard_competencies:
            for i, comp in enumerate(standard_competencies[:5]):
                # Limit length for better prompt context
                context_str += f"- {comp[:150]}...\n"
        else:
            # Dynamic fallback based on keywords if dictionary is empty
            top_kws = ", ".join([kw.keyword for kw in keywords[:3]])
            context_str += f"- {job_name} 전문가로서 {top_kws} 등을 활용한 업무 수행 능력\n"
            context_str += f"- 해당 직무 표준에 따른 효율적인 프로세스 관리 및 성과 창출"
        
        return JDContext(
            job_name=job_name,
            context=context_str,
            keywords=keywords
        )
