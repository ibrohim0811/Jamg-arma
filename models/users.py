import uuid
from enum import Enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, ForeignKey, DateTime, Boolean, func, BigInteger, Sequence, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


card_seq = Sequence("card_number_seq", start=1008000000000000)



class UserRole(str, Enum):
    CLIENT = "client"       # Oddiy mijoz (karta ochadi, pul o'tkazadi)
    ADMIN = "admin"


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(350))  # `:` ishlatildi
    last_name: Mapped[str] = mapped_column(String(350))   # `:` ishlatildi
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(13), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole), 
        default=UserRole.CLIENT, 
        nullable=False
    )
    # Bog'lanishlar
    device_tokens: Mapped[list["DeviceToken"]] = relationship("DeviceToken", back_populates="user", cascade="all, delete-orphan")
    credit_cards: Mapped[list["CreditCard"]] = relationship("CreditCard", back_populates="user", cascade="all, delete-orphan")


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # int qilindi
    token: Mapped[str] = mapped_column(String(500), unique=True, index=True, nullable=False)  # Firebase / APNs tokeni
    device_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'ios', 'android', 'web'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Userga Bog'lanish
    user: Mapped["Users"] = relationship("Users", back_populates="device_tokens")


class CreditCard(Base):
    __tablename__ = "credit_cards"  # Jadval nomi qo'shildi

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    card_number: Mapped[int] = mapped_column(
        BigInteger, 
        card_seq, 
        server_default=card_seq.next_value(), 
        unique=True, 
        index=True, 
        nullable=False
    )

    balance: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), default=Decimal("0.00"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Bog'lanish
    user: Mapped["Users"] = relationship("Users", back_populates="credit_cards")
    sent_transactions: Mapped[list["Transaction"]] = relationship("Transaction", foreign_keys="[Transaction.sender_card_id]", back_populates="sender_card")
    received_transactions: Mapped[list["Transaction"]] = relationship("Transaction", foreign_keys="[Transaction.receiver_card_id]", back_populates="receiver_card")

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    # Kimdan (CreditCard id ga bog'lanadi, agar tashqi manba yoki depozit bo'lsa NULL bo'lishi mumkin)
    sender_card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("credit_cards.id", ondelete="SET NULL"), nullable=True)
    
    # Kimga
    receiver_card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("credit_cards.id", ondelete="SET NULL"), nullable=True)
    
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="UZS", nullable=False)
    
    # Tranzaksiya holati: pending (jarayonda), success (muvaffaqiyatli), failed (xatolik)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    
    # Tranzaksiya turi: p2p, replenishment (hisobni to'ldirish), withdrawal (yechish)
    transaction_type: Mapped[str] = mapped_column(String(50), default="p2p", nullable=False)
    
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Izoh / xabarnoma
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Bog'lanishlar
    sender_card: Mapped["CreditCard"] = relationship("CreditCard", foreign_keys=[sender_card_id], back_populates="sent_transactions")
    receiver_card: Mapped["CreditCard"] = relationship("CreditCard", foreign_keys=[receiver_card_id], back_populates="received_transactions")