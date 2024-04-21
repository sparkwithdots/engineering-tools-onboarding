from utils.learning_object_search import persist_learning_objects
from rag.service_retriever import ServiceRetriever
import nest_asyncio

def main():
    
    nest_asyncio.apply()
    
    # Persist learning objects only once
    print("Persisting learning objects")
    persist_learning_objects()
    
    github_retriever = ServiceRetriever(service="github")
    launchdarkly_retriever = ServiceRetriever(service="launchdarkly")
    snyk_retriever = ServiceRetriever(service="snyk")
    
    print("Loading github documents")
    github_retriever.load_documents()
    print("Loading launchdarkly documents")
    launchdarkly_retriever.load_documents()
    print("Loading snyk documents")
    snyk_retriever.load_documents()
    
    # Run persist only once after data is stored
    print("Persisting github documents")
    github_retriever.persist()
    print("Persisting launchdarkly documents")
    launchdarkly_retriever.persist()
    print("Persisting snyk documents")
    snyk_retriever.persist()
    print("All data is prepared")

if __name__ == "__main__":
    main()