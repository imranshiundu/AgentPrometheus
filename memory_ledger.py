import chromadb
from datetime import datetime
import os

class ExperienceLedger:
    def __init__(self, db_path="./workspace/hive_mind_db"):
        """Initializes the persistent memory node."""
        chroma_host = os.getenv("CHROMA_HOST")
        
        if chroma_host:
            # Connect to the remote ChromaDB container (Titan Class)
            self.client = chromadb.HttpClient(host=chroma_host, port=8000)
            print(f"🧠 Hive Mind connected to remote ChromaDB at {chroma_host}:8000")
        else:
            # Fallback to local persistent storage
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.client = chromadb.PersistentClient(path=db_path)
            print(f"🧠 Hive Mind initialized with local storage at {db_path}")

        self.collection = self.client.get_or_create_collection(name="agent_lessons")

    def record_lesson(self, task_context: str, what_failed: str, the_fix: str) -> str:
        """
        Agents use this tool AFTER finally solving a difficult bug or task.
        """
        lesson_id = f"lesson_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 🧪 MATHEMATICAL OPTIMIZATION: 
        # We ONLY embed the context so the vector math stays pure and high-recall.
        # The actual lessons (failures/fixes) are stored safely in the metadata.
        self.collection.add(
            documents=[task_context], 
            metadatas=[{
                "type": "system_learning",
                "failed_approach": what_failed,
                "successful_solution": the_fix
            }],
            ids=[lesson_id]
        )
        return f"SUCCESS: Lesson {lesson_id} permanently recorded to the Hive Mind."

    def get_advice(self, current_task: str, max_results: int = 2) -> str:
        """
        Agents use this tool BEFORE writing code or running commands.
        """
        try:
            # Search the database strictly against the clean context strings
            results = self.collection.query(
                query_texts=[current_task],
                n_results=max_results
            )
            
            # If the database is empty or no relevant matches are found
            if not results['documents'] or not results['documents'][0]:
                return "No prior experience found for this exact task. You may proceed."
            
            # Reconstruct the lesson format for the LLM to understand
            lessons = []
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                formatted_lesson = (
                    f"SIMILAR PAST TASK: {doc}\n"
                    f"WHAT WE TRIED & FAILED: {meta.get('failed_approach', 'N/A')}\n"
                    f"THE WORKING FIX: {meta.get('successful_solution', 'N/A')}\n"
                    f"---"
                )
                lessons.append(formatted_lesson)
            
            retrieved_lessons = "\n".join(lessons)
            return f"CRITICAL PAST LESSONS TO APPLY:\n{retrieved_lessons}"
            
        except Exception as e:
            return f"No prior experience found. (Error: {str(e)})"

# Example of how it runs:
if __name__ == "__main__":
    hive_mind = ExperienceLedger()
    
    # 1. An agent fixes a bug and records it
    hive_mind.record_lesson(
        task_context="Downloading video using yt-dlp on macOS",
        what_failed="The default pip install yt-dlp threw a certifi SSL error.",
        the_fix="Used 'brew install yt-dlp' instead of pip, which handles the local macOS SSL certificates correctly."
    )
    
    # 2. A week later, a new agent is asked to download a video
    advice = hive_mind.get_advice("Write a script to download a YouTube video on a Mac")
    print(advice)
