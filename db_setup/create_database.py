from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Define the database connection
DATABASE_URL = "sqlite:///data/parliament.db"

# Create an engine and base
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Define the Members table
class Member(Base):
    __tablename__ = 'members'
    member_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    constituency = Column(String)
    party = Column(String)
    province_name = Column(String)
    caucus_name = Column(String)
    preferred_language = Column(String)

    # Relationships
    roles = relationship("Role", back_populates="member")
    votes = relationship("Vote", back_populates="member")
    associations = relationship("ParliamentaryAssociation", back_populates="member")
    bills = relationship("Bill", back_populates="sponsor")

# Define the Roles table
class Role(Base):
    __tablename__ = 'roles'
    role_id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.member_id'))
    role_name = Column(String)
    role_type = Column(String)  # Committee Member, Caucus Role, etc.
    committee_name = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)

    # Relationships
    member = relationship("Member", back_populates="roles")

# Define the Votes table
class Vote(Base):
    __tablename__ = 'votes'
    vote_id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.member_id'))
    parliament_number = Column(Integer)
    session_number = Column(Integer)
    vote_topic = Column(String)
    subject = Column(Text)
    vote_result = Column(String)  # Agreed To, Negatived, etc.
    vote_date = Column(Date)
    member_vote = Column(String)  # Yea, Nay, etc.

    # Relationships
    member = relationship("Member", back_populates="votes")

# Define the Parliamentary Associations table
class ParliamentaryAssociation(Base):
    __tablename__ = 'parliamentary_associations'
    association_id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey('members.member_id'))
    association_name = Column(String)
    role_in_group = Column(String)  # Member or Executive Member

    # Relationships
    member = relationship("Member", back_populates="associations")

# Define the Bills table
class Bill(Base):
    __tablename__ = 'bills'
    bill_id = Column(Integer, primary_key=True)
    bill_number = Column(String)
    parliament_number = Column(Integer)
    session_number = Column(Integer)
    status = Column(String)
    sponsor_id = Column(Integer, ForeignKey('members.member_id'))
    chamber = Column(String)

    # Relationships
    sponsor = relationship("Member", back_populates="bills")
    bill_progress = relationship("BillProgress", back_populates="bill")

# Define the Bill Progress table
class BillProgress(Base):
    __tablename__ = 'bill_progress'
    progress_id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey('bills.bill_id'))
    status = Column(String)
    progress_date = Column(Date)

    # Relationships
    bill = relationship("Bill", back_populates="bill_progress")

# Create all tables
Base.metadata.create_all(engine)

# Set up session
Session = sessionmaker(bind=engine)
session = Session()

print("Database setup completed successfully.")