from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    internal_phone = Column(String(32), nullable=True)
    external_phone = Column(String(32), nullable=True)
    email = Column(String(255), nullable=True)
    birthday = Column(Date, nullable=True)
    status = Column(String(32), nullable=False, default="candidate")
    uses_it_equipment = Column(Boolean, default=False)
    external_id = Column(String(128), nullable=True)
    pass_number = Column(String(64), nullable=True)

    position = relationship("Position")
    department = relationship("Department", foreign_keys=[department_id])
    manager = relationship("Employee", remote_side=[id], foreign_keys=[manager_id])
