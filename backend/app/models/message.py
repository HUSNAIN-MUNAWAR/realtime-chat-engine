from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin, uuid_str

class Message(Base, TimestampMixin):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("sender_id", "client_message_id", name="uq_sender_client_message"),
        Index("ix_messages_room_created", "room_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    room_id: Mapped[str] = mapped_column(String(36), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    client_message_id: Mapped[str] = mapped_column(String(80), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    parent_message_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_label: Mapped[str] = mapped_column(String(40), default="clean", nullable=False)

class MessageDeliveryReceipt(Base, TimestampMixin):
    __tablename__ = "message_delivery_receipts"
    __table_args__ = (UniqueConstraint("message_id", "user_id", name="uq_delivery_receipt"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

class MessageReadReceipt(Base, TimestampMixin):
    __tablename__ = "message_read_receipts"
    __table_args__ = (UniqueConstraint("message_id", "user_id", name="uq_read_receipt"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

class MessageRiskScore(Base, TimestampMixin):
    __tablename__ = "message_risk_scores"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str] = mapped_column(String(40), nullable=False)
    model_version: Mapped[str] = mapped_column(String(80), nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
