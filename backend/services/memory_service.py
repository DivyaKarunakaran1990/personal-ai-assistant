from sqlalchemy.orm import Session

from models import Memory


def save_memory(
    db: Session,
    category: str,
    content: str
):
    memory = Memory(
        category=category,
        content=content
    )

    db.add(memory)
    db.commit()
    db.refresh(memory)

    return memory


def get_memories(db: Session):
    return db.query(Memory).all()


def search_memory(
    db: Session,
    query: str
):
    memories = db.query(Memory).all()

    query_words = query.lower().split()

    results = []

    for memory in memories:
        content = memory.content.lower()

        score = sum(
            1 for word in query_words
            if word in content
        )

        if score > 0:
            results.append((score, memory))

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [memory for score, memory in results]