from sqlalchemy import Column, Integer, String, Text, Boolean
from database import Base



class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True)
    content = Column(Text)


class ShoppingItem(Base):
    __tablename__ = "shopping_items"

    id = Column(Integer, primary_key=True, index=True)
    item = Column(String, nullable=False)
    completed = Column(Boolean, default=False)

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)