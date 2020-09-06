import json
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    DateTime,
    ForeignKey, 
    Integer,
    String,
    Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import TypeDecorator

Base = declarative_base()

class TextPickleType(TypeDecorator):
    """
    Dumping and Loading JSON data (python dictionary)
    """
    impl = Text(256)

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


# Database Models
class Tweet(Base):
    __tablename__ = 'tweet'
    id = Column(Integer, primary_key=True)
    tweet_id = Column(String(25))
    parent_tweet_id = Column(String(25))  # only if replying to a tweet
    timestamp = Column(DateTime, default=datetime.utcnow)
    content = Column(String(240))
    tweet_data = Column(TextPickleType())

    def __repr__(self):
        return f'<Tweet: {self.tweet_id}>'

    def serialized(self):
        '''
        Returns table data in dictionary format
        '''
        return {
            'id': self.id,
            'tweet_id': self.tweet_id,
            'parent_tweet_id': self.parent_tweet_id,
            'timestamp': self.timestamp,
            'content': self.content,
            'tweet_data': self.tweet_data
        }


class Asset(Base):
    __tablename__ = 'asset'
    id = Column(Integer, primary_key=True)
    ticker = Column(String(5), unique=True)
    price_history = relationship("PriceHistory", back_populates="asset")

    def __repr__(self):
        return f'<Asset: {self.ticker}>'

    def serialized(self):
        '''
        Returns table data in dictionary format
        '''
        return {
            'id': self.id,
            'ticker': self.ticker,
            'price_history': [h.serialized() for h in self.price_history]
        }


class PriceHistory(Base):
    __tablename__ = 'pricehistory'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('asset.id'))
    asset = relationship("Asset", back_populates="price_history")
    price = Column(Integer)  # in pennies
    price_sats = Column(Integer)  # in sats
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PriceHistory: {self.asset.ticker}>'

    def serialized(self):
        '''
        Returns table data in dictionary format
        '''
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'price': self.price,
            'price_sats': self.price_sats,
            'timestamp': self.timestamp
        }


def initialize_database():
    '''
    Initialize the database and create the tables, return session maker
    '''
    engine = create_engine('sqlite:///app.db')
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    assets = session.query(Asset).all()
    if not assets:
        btc = Asset(ticker='BTC')
        spy = Asset(ticker='SPY')
        session.add(btc)
        session.add(spy)
        session.commit()
    session.close()
    return Session
