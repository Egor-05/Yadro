import pytest
from fastapi.testclient import TestClient
from main import app
from models import Node, Edge
from database import SessionLocal
from sqlalchemy import func

client = TestClient(app)


def cleaner(graph_id):
    with (SessionLocal() as db):
        for i in db.query(Node).filter(Node.graph_id == graph_id).all():
            db.delete(i)
        db.commit()


@pytest.fixture(scope="session", autouse=True)
def populate_db():
    with SessionLocal() as db:
        graph_id = db.query(func.max(Node.graph_id)).scalar()
        if graph_id is None:
            graph_id = -1
        graph_id += 1

        nodes = [
            Node(name="a", graph_id=graph_id),
            Node(name="b", graph_id=graph_id),
            Node(name="c", graph_id=graph_id),
            Node(name="d", graph_id=graph_id)
        ]
        db.add_all(nodes)
        db.commit()

        edges = [
            Edge(source_node_id=nodes[0].id, target_node_id=nodes[2].id),
            Edge(source_node_id=nodes[1].id, target_node_id=nodes[2].id),
            Edge(source_node_id=nodes[2].id, target_node_id=nodes[3].id)
        ]
        db.add_all(edges)
        db.commit()

    yield graph_id
    cleaner(graph_id)


def test_pcreate_graph_positive():
    graph_data = {
        "nodes": [
            {"name": "A"},
            {"name": "B"},
            {"name": "C"}
        ],
        "edges": [
            {
                "source": "A",
                "target": "B"
            },
            {
                "source": "B",
                "target": "C"
            }
        ]
    }
    response = client.post("/api/graph/", json=graph_data)
    assert response.status_code == 201
    data = response.json()
    assert isinstance(data["id"], int)
    cleaner(data["id"])


def test_create_graph_with_duplicate_nodes():
    graph_data = {
        "nodes": [
            {"name": "A"},
            {"name": "A"}
        ],
        "edges": [
            {
                "source": "A",
                "target": "A"
            }
        ]
    }
    response = client.post("/api/graph/", json=graph_data)
    assert response.status_code == 400
    assert response.json()["message"] == "Duplicate node names"


def test_create_graph_with_nonexistent_node():
    graph_data = {
        "nodes": [
            {"name": "A"},
            {"name": "B"}
        ],
        "edges": [
            {
                "source": "A",
                "target": "C"
            }
        ]
    }
    response = client.post("/api/graph/", json=graph_data)
    assert response.status_code == 400
    assert response.json()["message"] == "Non-existent node in the edge"

def test_create_cyclic_graph():
    graph_data = {
        "nodes": [
            {"name": "A"},
            {"name": "B"},
            {"name": "C"}
        ],
        "edges": [
            {
                "source": "A",
                "target": "B"
            },
            {
                "source": "B",
                "target": "C"
            },
            {
                "source": "C",
                "target": "A"
            }
        ]
    }
    response = client.post("/api/graph/", json=graph_data)
    assert response.status_code == 400
    assert response.json()["message"] == "Graph can't contain cycles"


def test_get_graph_positive(populate_db):
    nodes = [
        {"name":"a"},
        {"name":"b"},
        {"name":"c"},
        {"name":"d"}
    ]
    edges = [
        {
            "source":"a",
            "target":"c"
        },
        {
            "source":"b",
            "target":"c"
        },
        {
            "source":"c",
            "target":"d"
        }
    ]

    response = client.get(f"/api/graph/{populate_db}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == populate_db
    assert data["nodes"] == nodes
    assert data["edges"] == edges


def test_get_graph_negative():
    response = client.get("/api/graph/9999")
    assert response.status_code == 404
    assert response.json()["message"] == "Graph not found"


def test_get_graph_with_invalid_format_id():
    response = client.get("/api/graph/qwerty")
    assert response.status_code == 422


def test_get_adjacency_list_positive(populate_db):
    response = client.get(f"/api/graph/{populate_db}/adjacency_list")
    assert response.status_code == 200
    data = response.json()
    assert data["adjacency_list"]["a"] == ["c"]
    assert data["adjacency_list"]["b"] == ["c"]
    assert data["adjacency_list"]["c"] == ["d"]
    assert data["adjacency_list"]["d"] == []


def test_get_adjacency_list_negative():
    response = client.get("/api/graph/9999/adjacency_list")
    assert response.status_code == 404
    assert response.json()["message"] == "Graph not found"


def test_get_adjacency_list_graph_with_invalid_format_id():
    response = client.get("/api/graph/qwerty/adjacency_list")
    assert response.status_code == 422


def test_get_reverse_adjacency_list_positive(populate_db):
    response = client.get(f"/api/graph/{populate_db}/reverse_adjacency_list")
    assert response.status_code == 200
    data = response.json()
    assert data["adjacency_list"]["a"] == []
    assert data["adjacency_list"]["b"] == []
    assert data["adjacency_list"]["c"] == ["a", "b"]
    assert data["adjacency_list"]["d"] == ["c"]


def test_get_reverse_adjacency_list_negative():
    response = client.get("/api/graph/9999/reverse_adjacency_list")
    assert response.status_code == 404
    assert response.json()["message"] == "Graph not found"


def test_get_reverse_adjacency_list_graph_with_invalid_format_id():
    response = client.get("/api/graph/qwerty/reverse_adjacency_list")
    assert response.status_code == 422


def test_delete_graph_positive(populate_db):
    response = client.delete(f"/api/graph/{populate_db}/node/a")
    assert response.status_code == 204
    with SessionLocal() as db:
        assert db.query(Node).filter(Node.graph_id == populate_db, Node.name == "a").first() is None


def test_delete_graph_negative_wrong_graph_id():
    response = client.delete("/api/graph/9999/node/a")
    assert response.status_code == 404
    assert response.json()["message"] == "Node doesn't exists"


def test_delete_graph_negative_wrong_node_name(populate_db):
    response = client.delete(f"/api/graph/{populate_db}/node/qwerty")
    assert response.status_code == 404
    assert response.json()["message"] == "Node doesn't exists"


def test_delete_graph_with_invalid_graph_id_format():
    response = client.delete("/api/graph/qwerty/node/a")
    assert response.status_code == 422
