from langchain_openai import OpenAIEmbeddings
from typing import List
from configs import Configs
import pandas as pd
import os
import ast
import numpy as np

def embed_text(text: str, model: str = "text-embedding-ada-002") -> List[float]:
    embeddings = OpenAIEmbeddings(model=model)
    query_result = embeddings.embed_query(text)
    return query_result

def cosine_similarity(a: List[float], b: List[float]) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def persist_learning_objects():
    learning_object_data = "data/learning_objects_with_embedding.csv"
    if os.path.exists(learning_object_data):
        return
    data = []
    for service, config in Configs.learningpath_configs()["services"].items():
        for item in config["learningObjects"]:
            data.append({
                "service": service,
                "topic": item["topic"],
                "description": item["description"],
                "level": item["level"],
                "topic_desc": item["topic"] + "\n\n" + item["description"]
            })
    df = pd.DataFrame(data)
    df["embeddings"] = df["topic_desc"].apply(embed_text)
    df.to_csv(learning_object_data, index=False)

def generate_learning_objects_dataframe() -> pd.DataFrame:
    learning_object_data = "data/learning_objects_with_embedding.csv"
    df = pd.read_csv(learning_object_data)
    df["vector"] = df["embeddings"].apply(ast.literal_eval)
    return df
    # if os.path.exists(learning_object_data):      
    #     df =  pd.read_csv(learning_object_data)
    #     df["vector"] = df["embeddings"].apply(ast.literal_eval)
    #     return df
    # data = []
    # for service, config in Configs.learningpath_configs()["services"].items():
    #     for item in config["learningObjects"]:
    #         data.append({
    #             "service": service,
    #             "topic": item["topic"],
    #             "description": item["description"],
    #             "level": item["level"],
    #             "topic_desc": item["topic"] + "\n\n" + item["description"]
    #         })
    # df = pd.DataFrame(data)
    # df["embeddings"] = df["topic_desc"].apply(embed_text)
    # df.to_csv(learning_object_data, index=False)
    # df["vector"] = df["embeddings"]
    # return df

def search_learning_objects(service: str, queries: List[str], df: pd.DataFrame, top_n: int = 3) -> List[str]:
    df_temp = df.copy()
    df_temp = df_temp[df_temp["service"] == service]
    results = {}
    for query in queries:
        query_vector = embed_text(query)
        df1 = df_temp.copy()
        df1["similarity"] = df1["vector"].apply(lambda x: cosine_similarity(x, query_vector))
        query_results = df1.sort_values(by="similarity", ascending=False).head(top_n)["topic"].values.tolist()
        for result in query_results:
            if result not in results:
                results[result] = 1
    return list(results.keys())
