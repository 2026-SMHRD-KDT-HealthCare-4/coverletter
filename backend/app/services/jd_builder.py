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
            return data.get("wantedRoot", {}).get("wanted", [])
        except Exception as e:
            print(f"Error fetching recruitment data: {e}")
            return []

    def extract_keywords(self, job_descriptions: List[str]):
        if not job_descriptions:
            return []
        
        vectorizer = TfidfVectorizer(max_features=15)
        tfidf_matrix = vectorizer.fit_transform(job_descriptions)
        feature_names = vectorizer.get_feature_names_out()
        
        # Calculate average score for each keyword
        scores = tfidf_matrix.mean(axis=0).tolist()[0]
        keywords = []
        for name, score in zip(feature_names, scores):
            keywords.append(JDKeyword(keyword=name, frequency=score))
        
        # Sort by frequency
        keywords.sort(key=lambda x: x.frequency, reverse=True)
        return keywords

    def clean_text(self, text: str):
        if not text:
            return ""
        # Remove HTML tags and special characters
        text = re.sub(r'<[^>]*>', '', text)
        text = re.sub(r'[^\w\s]', '', text)
        return text

    async def build_context(self, job_name: str) -> JDContext:
        raw_wanted = self.fetch_recruitment_data(job_name)
        
        job_descs = []
        full_context_parts = []
        
        for item in raw_wanted:
            # In a real scenario, we might need to call the Detail API for each item
            # For the prototype, we use what's available in the List API or mock detail
            title = item.get("wantedTitle", "")
            company = item.get("company", "")
            # Mocking more detail since List API is limited
            desc = f"{title} at {company}. 요구역량: {job_name} 관련 기술 및 경험."
            job_descs.append(self.clean_text(desc))
            
        keywords = self.extract_keywords(job_descs)
        
        # Build the final context string
        context_str = f"직종: {job_name}\n\n"
        context_str += "시장 주요 요구 사항:\n"
        for kw in keywords:
            context_str += f"- {kw.keyword}\n"
        
        # In a real implementation, we would also merge NCS/Job Dictionary data here
        context_str += "\n표준 직무 역량: 사용자 요구사항 분석, 컴포넌트 구조화, UI 설계서 작성."
        
        return JDContext(
            job_name=job_name,
            context=context_str,
            keywords=keywords
        )
