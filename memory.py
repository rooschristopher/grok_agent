import chromadb
from typing import List, Dict, Any, Optional

class ChromaMemory:
    def __init__(self, persist_directory: str):
        chroma_client = chromadb.PersistentClient(path=persist_directory)
        self.chats_coll = chroma_client.get_or_create_collection(
            name="chats",
            metadata={"hnsw:space": "cosine"}
        )
        self.agent_coll = chroma_client.get_or_create_collection(
            name="agent_memory",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chat_messages(self, chat_id: str, messages: List[Dict[str, Any]]):
        documents = []
        metadatas = []
        ids = []
        for i, msg in enumerate(messages):
            content = msg.get('content', '')[:1500]  # truncate
            doc = f"{msg['role']}: {content}"
            documents.append(doc)
            metadatas.append({
                "chat_id": chat_id,
                "role": msg['role'],
                "turn": i
            })
            ids.append(f"c_{chat_id}_{i}")
        if documents:
            self.chats_coll.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

    def query_chats(self, query: str, n_results: int = 5) -> dict:
        return self.chats_coll.query(
            query_texts=[query],
            n_results=n_results
        )

    def add_agent_experience(self, goal: str, outcome: str, tools_used: Optional[List[str]] = None):
        doc = f"Goal: {goal[:800]}\nOutcome: {outcome[:1200]}\nTools used: {', '.join(tools_used or [])}"
        metadata = {
            "type": "experience",
            "goal_snippet": goal[:200]
        }
        doc_id = f"exp_{abs(hash(goal[:500]))}"
        self.agent_coll.add(
            documents=[doc],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def query_agent_memory(self, query: str, n_results: int = 5) -> dict:
        return self.agent_coll.query(
            query_texts=[query],
            n_results=n_results
        )
