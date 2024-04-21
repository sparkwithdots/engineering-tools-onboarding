from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.storage._lc_store import create_kv_docstore
from langchain.storage.file_system import LocalFileStore
from langchain.retrievers import ParentDocumentRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.pdf import PyMuPDFLoader
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain_community.document_loaders.gitbook import GitbookLoader
from configs import Configs

class ServiceRetriever():
    
    def __init__(self, service: str, embedding_model: str = "text-embedding-ada-002", parent_chunk_size: int=1000, child_chunk_size: int=200, chunk_overlap: int=30):
        self.service = service
        self.embedding_func = OpenAIEmbeddings(model=embedding_model)
        self.vectorstore = Chroma(
           persist_directory="data/vectorstore",
           collection_name=f"{service}_query",
           embedding_function=self.embedding_func,
        )
        self.local_store = LocalFileStore(f"data/docstore/{service}_query")
        self.docstore = create_kv_docstore(self.local_store)
        self.parent_splitter = RecursiveCharacterTextSplitter(chunk_size=parent_chunk_size, chunk_overlap=chunk_overlap)
        self.child_splitter = RecursiveCharacterTextSplitter(chunk_size=child_chunk_size, chunk_overlap=chunk_overlap)
        self.documents = []
        self.retriever = None
    
    def load_documents(self):
        service_retrievers = Configs.get_service_config(service = self.service, config="rag", key="retrievers")
        for item in service_retrievers:
            type, paths = item["type"], item["paths"]
            if type == "pdf":
                for path in paths:
                    pdf_loader = PyMuPDFLoader(file_path=path)
                    docs = pdf_loader.load()
                    self.documents.extend(docs)
                    print(f"Loaded {len(docs)} PDF documents for {self.service}")
            elif type == "web":
                web_loader = WebBaseLoader(paths)
                docs = web_loader.aload()
                self.documents.extend(docs)
                print(f"Loaded {len(docs)} web documents for {self.service}")
            elif type == "gitbook":
                # Provide the base path of the gitbook
                gitbook_loader = GitbookLoader(paths[0], load_all_paths=True, continue_on_failure=True)
                docs = gitbook_loader.load()
                self.documents.extend(docs)
                print(f"Loaded {len(docs)} gitbook documents for {self.service}")
        # More loaders can be added here
        
    def get_retriever(self, search_type: str="mmr", top_k: int=2):
        self.retriever = ParentDocumentRetriever(
            name=f"{self.service}_retriever",
            vectorstore=self.vectorstore,
            docstore=self.docstore,
            parent_splitter=self.parent_splitter,
            child_splitter=self.child_splitter,
            search_type=search_type,
            search_kwargs={"k": top_k},
        )
        return self.retriever
    
    def persist(self, search_type: str="mmr", top_k: int=2):
        if not self.documents or len(self.documents) == 0:
            raise ValueError("No documents to persist")
        if self.retriever is None:
            self.retriever = self.get_retriever(search_type=search_type, top_k=top_k)
        self.vectorstore.persist()
        self.retriever.add_documents(self.documents)