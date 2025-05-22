from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Node(Base):
    __tablename__ = 'nodes'

    id = Column(Integer, primary_key=True)
    graph_id = Column(Integer)
    name = Column(String(255))

    outgoing_edges = relationship(
        "Edge",
        foreign_keys="Edge.source_node_id",
        back_populates="source_node",
        cascade="all,delete"
    )

    incoming_edges = relationship(
        "Edge",
        foreign_keys="Edge.target_node_id",
        back_populates="target_node",
        cascade="all,delete"
    )


class Edge(Base):
    __tablename__ = 'edges'

    id = Column(Integer, primary_key=True)
    source_node_id = Column(Integer, ForeignKey('nodes.id'))
    target_node_id = Column(Integer, ForeignKey('nodes.id'))

    source_node = relationship(
        "Node",
        foreign_keys=[source_node_id],
        back_populates="outgoing_edges"
    )

    target_node = relationship(
        "Node",
        foreign_keys=[target_node_id],
        back_populates="incoming_edges"
    )
