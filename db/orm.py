from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from .connection import DBConnection

base = declarative_base()

class WikiParagraphs(base):

    __tablename__ = 'wiki_articles_paragraphs'

    id = Column(Integer , primary_key=True)
    paragraph = Column(String)
    url = Column(String)
    tag = Column(String)
    input_time = Column(DateTime(timezone=True), default=func.now())

    def __init__(self, paragraph: str, url: str, tag: str) -> None:
        self.paragraph = paragraph
        self.url = url
        self.tag = tag

class WikiDB(DBConnection):
    
    def __init__(self) -> None:
        super().__init__()

    def add_record(self, infos: list) -> None:
        # Input new data on DB
        record = WikiParagraphs(**infos)

        sess = self.get_session()

        sess.add(record)
        sess.commit()