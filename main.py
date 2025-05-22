from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from sqlalchemy import func

from database import SessionLocal
from models import Node, Edge

app = FastAPI()


class NodeData(BaseModel):
    name: str

class EdgeData(BaseModel):
    source: str
    target: str


class GraphData(BaseModel):
    nodes: List[NodeData]
    edges: List[EdgeData]


def is_acyclic(node, visited, graph):
    for i in graph[node]:
        if i not in visited:
            return is_acyclic(i, visited | {i}, graph)
        else:
            return False
    return True


def graph_data_validation(graph_data):
    graph = {}
    for node in graph_data.nodes:
        if node.name in graph:
            return "Duplicate node names"
        graph[node.name] = []
    for edge in graph_data.edges:
        if edge.source not in graph or edge.target not in graph:
            return "Non-existent node in the edge"
        graph[edge.source].append(edge.target)
    for i in graph:
        if not is_acyclic(i, set(), graph):
            return "Graph can't contain cycles"
    return ""


@app.post("/api/graph", status_code=201)
def create_graph(graph_data: GraphData):
    message = graph_data_validation(graph_data)
    if message:
        return JSONResponse(content={"message": message}, status_code=400)
    with SessionLocal() as db:
        nodes = {}
        graph_id = db.query(func.max(Node.graph_id)).scalar()
        if graph_id is None:
            graph_id = -1
        graph_id += 1

        for node in graph_data.nodes:
            new_node = Node(
                name=node.name,
                graph_id=graph_id
            )
            db.add(new_node)
            nodes[node.name] = new_node

        db.flush()

        for edge in graph_data.edges:
            new_edge = Edge(
                source_node_id=nodes[edge.source].id,
                target_node_id=nodes[edge.target].id,
            )
            db.add(new_edge)
        db.commit()
        return {"id": graph_id}


@app.get("/api/graph/{graph_id}")
def get_graph(graph_id: int):
    with SessionLocal() as db:
        nodes = db.query(Node).filter(Node.graph_id == graph_id).all()
        if not nodes:
            return JSONResponse(content={"message": "Graph not found"}, status_code=404)
        response = {
            "id": graph_id,
            "nodes": [],
            "edges": []
        }
        for node in nodes:
            response["nodes"].append({"name": node.name})
            for edge in node.outgoing_edges:
                response["edges"].append(
                    {
                        "source": edge.source_node.name,
                        "target": edge.target_node.name
                    }
                )
        return response


@app.get("/api/graph/{graph_id}/adjacency_list")
def get_adjacency_list(graph_id: int):
    with SessionLocal() as db:
        nodes = db.query(Node).filter(Node.graph_id == graph_id).all()
        if not nodes:
            return JSONResponse(content={"message": "Graph not found"}, status_code=404)
        response = {
            "adjacency_list": {}
        }
        for node in nodes:
            connected_nodes = []
            for edge in node.outgoing_edges:
                connected_nodes.append(edge.target_node.name)
            response["adjacency_list"][node.name] = connected_nodes
        return response


@app.get("/api/graph/{graph_id}/reverse_adjacency_list")
def get_reverse_adjacency_list(graph_id: int):
    with SessionLocal() as db:
        nodes = db.query(Node).filter(Node.graph_id == graph_id).all()
        if not nodes:
            return JSONResponse(content={"message": "Graph not found"}, status_code=404)
        response = {
            "adjacency_list": {}
        }
        for node in nodes:
            connected_nodes = []
            for edge in node.incoming_edges:
                connected_nodes.append(edge.source_node.name)
            response["adjacency_list"][node.name] = connected_nodes
        return response
    
    
@app.delete("/api/graph/{graph_id}/node/{node_name}", status_code=204)
def delete_node(graph_id: int, node_name: str):
    with SessionLocal() as db:
        obj = db.query(Node).filter(
            Node.graph_id == graph_id,
            Node.name == node_name
        ).first()
        if obj:
            db.delete(obj)
            db.commit()
        else:
            return JSONResponse(content={"message": "Node doesn't exists"}, status_code=404)
