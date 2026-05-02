import re
from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader

from app.schemas.resume_import import ResumeImportRead
from app.services.analysis.rules import SKILL_PATTERNS


class ResumeImportService:
    async def parse_upload(self, file: UploadFile) -> ResumeImportRead:
        if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF resume uploads are supported.")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded PDF is empty.")

        text = self._extract_pdf_text(content)
        if not text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not extract text from this PDF.")

        return ResumeImportRead(
            resume_text=text[:30000],
            skills_suggestions=self._skills(text),
            projects_suggestions=self._projects(text),
            experience_summary_suggestion=self._experience_summary(text),
        )

    def _extract_pdf_text(self, content: bytes) -> str:
        try:
            reader = PdfReader(BytesIO(content))
            page_text = [page.extract_text() or "" for page in reader.pages]
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not read this PDF.") from exc
        return self._clean_text("\n".join(page_text))

    def _skills(self, text: str) -> list[str]:
        found: list[str] = []
        for skill, patterns in SKILL_PATTERNS.items():
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                found.append(skill)
        return found

    def _projects(self, text: str) -> list[str]:
        candidates: list[str] = []
        for line in text.splitlines():
            clean_line = self._clean_text(re.sub(r"^[\-*•\s]+", "", line))
            if len(clean_line) < 20:
                continue
            if re.search(r"\b(built|developed|implemented|created|designed|launched|analyzed)\b", clean_line, re.IGNORECASE):
                candidates.append(clean_line[:300])
            elif re.match(r"^[\-*•]", line.strip()):
                candidates.append(clean_line[:300])
        return self._unique(candidates)[:5]

    def _experience_summary(self, text: str) -> str:
        sentences = [
            self._clean_text(sentence)
            for sentence in re.split(r"(?<=[.!?])\s+|\n+", text)
            if len(self._clean_text(sentence).split()) >= 6
        ]
        return " ".join(sentences[:3])[:5000]

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            key = value.lower()
            if key not in seen:
                seen.add(key)
                result.append(value)
        return result
