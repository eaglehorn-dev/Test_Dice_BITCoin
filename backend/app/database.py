"""
Database models and session management
SQLAlchemy ORM models for the dice game
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from .config import config

# Create engine
engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {},
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Session:
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    """User accounts and wallet addresses"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Statistics
    total_bets = Column(Integer, default=0)
    total_wagered = Column(Integer, default=0)  # in satoshis
    total_won = Column(Integer, default=0)
    total_lost = Column(Integer, default=0)
    
    # Relationships
    bets = relationship("Bet", back_populates="user")
    seeds = relationship("Seed", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.address}>"


class Seed(Base):
    """Server and client seeds for provably fair system"""
    __tablename__ = "seeds"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Server seed (hidden until reveal)
    server_seed = Column(String(128), nullable=False)
    server_seed_hash = Column(String(128), nullable=False)  # SHA256 hash shown to user
    
    # Client seed
    client_seed = Column(String(128), nullable=False)
    
    # Nonce counter
    nonce = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    revealed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="seeds")
    bets = relationship("Bet", back_populates="seed")
    
    __table_args__ = (
        Index('idx_seed_user_active', 'user_id', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Seed {self.id} user={self.user_id} nonce={self.nonce}>"


class Bet(Base):
    """Individual bet records"""
    __tablename__ = "bets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seed_id = Column(Integer, ForeignKey("seeds.id"), nullable=False)
    
    # Bet details
    bet_amount = Column(Integer, nullable=False)  # satoshis
    target_multiplier = Column(Float, nullable=False)
    win_chance = Column(Float, nullable=False)  # percentage
    
    # Result
    nonce = Column(Integer, nullable=False)
    roll_result = Column(Float, nullable=True)  # 0.00 - 99.99
    is_win = Column(Boolean, nullable=True)
    payout_amount = Column(Integer, nullable=True)  # satoshis
    profit = Column(Integer, nullable=True)  # satoshis (can be negative)
    
    # Transaction tracking
    deposit_txid = Column(String(64), index=True, nullable=True)
    deposit_address = Column(String(64), index=True, nullable=True)
    payout_txid = Column(String(64), index=True, nullable=True)
    
    # Status tracking
    status = Column(String(20), default="pending")  # pending, confirmed, rolled, paid, failed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    rolled_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="bets")
    seed = relationship("Seed", back_populates="bets")
    transaction = relationship("Transaction", back_populates="bet", uselist=False)
    payout = relationship("Payout", back_populates="bet", uselist=False)
    
    __table_args__ = (
        Index('idx_bet_user_created', 'user_id', 'created_at'),
        Index('idx_bet_status', 'status'),
        Index('idx_bet_deposit_txid', 'deposit_txid'),
    )
    
    def __repr__(self):
        return f"<Bet {self.id} user={self.user_id} amount={self.bet_amount} status={self.status}>"


class Transaction(Base):
    """Transaction detection and state tracking"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    txid = Column(String(64), unique=True, index=True, nullable=False)
    bet_id = Column(Integer, ForeignKey("bets.id"), nullable=True)
    
    # Transaction details
    from_address = Column(String(64), index=True, nullable=True)
    to_address = Column(String(64), index=True, nullable=False)
    amount = Column(Integer, nullable=False)  # satoshis
    fee = Column(Integer, nullable=True)
    
    # Detection metadata
    detected_by = Column(String(50), nullable=False)  # websocket, manual, api
    detection_count = Column(Integer, default=1)  # how many times we detected this
    
    # Blockchain status
    confirmations = Column(Integer, default=0)
    block_height = Column(Integer, nullable=True)
    block_hash = Column(String(64), nullable=True)
    
    # State tracking
    is_processed = Column(Boolean, default=False)
    is_duplicate = Column(Boolean, default=False)
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Raw data for debugging
    raw_data = Column(Text, nullable=True)  # JSON string
    
    # Relationships
    bet = relationship("Bet", back_populates="transaction")
    
    __table_args__ = (
        Index('idx_tx_to_address', 'to_address'),
        Index('idx_tx_processed', 'is_processed'),
        Index('idx_tx_detected_by', 'detected_by'),
    )
    
    def __repr__(self):
        return f"<Transaction {self.txid[:8]}... amount={self.amount} conf={self.confirmations}>"


class Payout(Base):
    """Payout records and tracking"""
    __tablename__ = "payouts"
    
    id = Column(Integer, primary_key=True, index=True)
    bet_id = Column(Integer, ForeignKey("bets.id"), nullable=False)
    
    # Payout details
    amount = Column(Integer, nullable=False)  # satoshis
    to_address = Column(String(64), nullable=False)
    txid = Column(String(64), unique=True, index=True, nullable=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, broadcast, confirmed, failed
    error_message = Column(Text, nullable=True)
    
    # Fee tracking
    network_fee = Column(Integer, nullable=True)
    
    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    broadcast_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    
    # Relationships
    bet = relationship("Bet", back_populates="payout")
    
    __table_args__ = (
        Index('idx_payout_status', 'status'),
        Index('idx_payout_to_address', 'to_address'),
    )
    
    def __repr__(self):
        return f"<Payout {self.id} bet={self.bet_id} amount={self.amount} status={self.status}>"


class DepositAddress(Base):
    """Generated deposit addresses for users"""
    __tablename__ = "deposit_addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Address details
    address = Column(String(64), unique=True, index=True, nullable=False)
    derivation_path = Column(String(50), nullable=True)  # For HD wallets
    
    # Status
    is_active = Column(Boolean, default=True)
    is_used = Column(Boolean, default=False)
    
    # Expected bet parameters (optional)
    expected_multiplier = Column(Float, nullable=True)
    expected_amount_min = Column(Integer, nullable=True)
    expected_amount_max = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_deposit_active', 'is_active'),
        Index('idx_deposit_user_active', 'user_id', 'is_active'),
    )
    
    def __repr__(self):
        return f"<DepositAddress {self.address} user={self.user_id}>"


# Create all tables
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created successfully")


# Migration helper
def drop_all():
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
    print("[WARNING] All database tables dropped")
