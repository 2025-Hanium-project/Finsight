from sentence_transformers import SentenceTransformer

MODEL_NAME = 'jhgan/ko-sroberta-multitask'
model = SentenceTransformer(MODEL_NAME)

def get_embedding(text: str):
    return model.encode(text).tolist()
