from sqlalchemy.orm import Session

from models import Document


def search_documents(db: Session, query: str):

    documents = db.query(Document).all()

    query_words = query.lower().split()

    results = []

    for document in documents:

        content_lower = document.content.lower()

        score = sum(
            1
            for word in query_words
            if word in content_lower
        )

        if score > 0:
            results.append({
                "id": document.id,
                "filename": document.filename,
                "content": document.content,
                "score": score
            })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:3]