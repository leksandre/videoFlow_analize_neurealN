import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import faiss
import re

# 1. Парсинг данных с сайтов
def parse_domotel_pages():
    urls = [
        "https://xn--d1acscjb2a6f.xn--p1ai/",
        "https://xn--80az8a.xn--d1aqf.xn--p1ai/%D1%81%D0%B5%D1%80%D0%B2%D0%B8%D1%81%D1%8B/%D0%BA%D0%B0%D1%82%D0%B0%D0%BB%D0%BE%D0%B3-%D0%BD%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D1%80%D0%BE%D0%B5%D0%BA/%D0%BE%D0%B1%D1%8A%D0%B5%D0%BA%D1%82/58154",
        "https://xn--80az8a.xn--d1aqf.xn--p1ai/%D1%81%D0%B5%D1%80%D0%B2%D0%B8%D1%81%D1%8B/%D0%B5%D0%B4%D0%B8%D0%BD%D1%8B%D0%B9-%D1%80%D0%B5%D0%B5%D1%81%D1%82%D1%80-%D0%B7%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D1%89%D0%B8%D0%BA%D0%BE%D0%B2/%D0%B7%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D1%89%D0%B8%D0%BA/17697"
    ]
    
    knowledge_base = []
    
    for url in urls:
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Удаляем ненужные элементы
            for element in soup(['script', 'style', 'nav', 'footer', 'iframe']):
                element.decompose()
                
            # Основной контент страницы
            text = soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)  # Удаляем множественные пробелы
            
            # Структурируем данные
            page_data = {
                "url": url,
                "title": soup.title.string if soup.title else url,
                "content": text[:10000]  # Ограничиваем длину
            }
            
            knowledge_base.append(page_data)
            
        except Exception as e:
            print(f"Ошибка при парсинге {url}: {str(e)}")
    
    return knowledge_base

# 2. Создание векторного индекса
def create_vector_index(knowledge_base):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Подготовка данных для индексации
    documents = []
    for item in knowledge_base:
        # Разбиваем текст на чанки по 500 символов
        text = item['content']
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        
        for chunk in chunks:
            documents.append({
                "text": chunk,
                "source": item['url'],
                "title": item['title']
            })
    
    # Генерация эмбеддингов
    embeddings = model.encode([doc['text'] for doc in documents], show_progress_bar=True)
    
    # Создание FAISS индекса
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    
    return index, documents, model

# 3. Сохранение базы знаний
def save_knowledge_base(index, documents, model):
    # Сохраняем индекс
    faiss.write_index(index, "domotel_index.faiss")
    
    # Сохраняем документы
    with open("domotel_documents.json", "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    # Сохраняем модель (опционально)
    model.save("domotel_sbert_model")

# 4. Загрузка базы знаний
def load_knowledge_base():
    index = faiss.read_index("domotel_index.faiss")
    
    with open("domotel_documents.json", "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    return index, documents, model

# 5. Поиск релевантных документов
def search(query, index, documents, model, top_k=3):
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, top_k)
    
    results = []
    for i in range(top_k):
        idx = indices[0][i]
        results.append({
            "text": documents[idx]['text'],
            "source": documents[idx]['source'],
            "title": documents[idx]['title'],
            "score": float(distances[0][i])
        })
    
    return results

# 6. Интеграция с Telegram ботом (дополнение к предыдущему коду)
class DomotelRAG:
    def __init__(self):
        self.index, self.documents, self.model = load_knowledge_base()
        
    def get_context(self, query):
        results = search(query, self.index, self.documents, self.model)
        context = "\n\n".join([f"Источник: {res['title']}\n{res['text']}" for res in results])
        return context

# Основной процесс создания базы знаний
if __name__ == "__main__":
    print("Создание базы знаний Домотель...")
    knowledge_base = parse_domotel_pages()
    index, documents, model = create_vector_index(knowledge_base)
    save_knowledge_base(index, documents, model)
    print("База знаний успешно создана!")