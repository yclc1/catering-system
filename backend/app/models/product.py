"""Product and ProductCategory models."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin


class ProductCategory(AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "product_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    products = relationship("Product", back_populates="category", lazy="selectin")


class Product(AuditMixin, SoftDeleteMixin, Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=False, index=True)
    unit = Column(String(16), nullable=False)
    spec = Column(String(64))
    default_supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    notes = Column(Text)

    category = relationship("ProductCategory", back_populates="products", lazy="selectin")
    default_supplier = relationship("Supplier", foreign_keys=[default_supplier_id], lazy="selectin")
