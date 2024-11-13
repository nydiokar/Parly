from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, Text, Enum, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum

# Define the database connection
DATABASE_URL = "sqlite:///data/parliament.db"

# Create an engine and base
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Define role type enums
class RoleType(enum.Enum):
    MEMBER_OF_PARLIAMENT = "Member of Parliament"
    POLITICAL_AFFILIATION = "Political Affiliation"
    COMMITTEE_MEMBER = "Committee Member"
    PARLIAMENTARY_ASSOCIATION = "Parliamentary Association"
    ELECTION_CANDIDATE = "Election Candidate"
    PARLIAMENTARIAN_OFFICE = "Parliamentarian Office"

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
    
    # Common fields for all roles
    role_type = Column(Enum(RoleType))
    person_honorific = Column(String)  # Official honorific title
    from_date = Column(Date)  # Last time elected/appointed
    to_date = Column(Date)   # End of mandate
    parliament_number = Column(String)
    session_number = Column(String)
    
    # MP/Constituency specific
    constituency_name = Column(String)
    constituency_province = Column(String)
    caucus_name = Column(String)  # Political party
    
    # Committee specific
    committee_name = Column(String)
    affiliation_role_name = Column(String)  # Member's role in committee
    
    # Parliamentary Associations specific
    organization_name = Column(String)
    association_role_type = Column(String)  # Association member's role

    # Offices and Roles as Parliamentarian specific
    office_role = Column(String)

    __table_args__ = (
        UniqueConstraint(
            'member_id', 'role_type', 'from_date',
            'parliament_number', 'session_number',
            'committee_name', 'organization_name',
            name='unique_role'
        ),
    )

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
