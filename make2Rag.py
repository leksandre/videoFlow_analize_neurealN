import os
import requests
from bs4 import BeautifulSoup
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

# ========== Конфигурация ==========
OUTPUT_DIR = "domotel_2var_documents"

URLS = [
    "https://xn--d1acscjb2a6f.xn--p1ai/", 
    "https://xn--80az8a.xn--d1aqf.xn--p1ai/%D1%81%D0%B5%D1%80%D0%B2%D0%B8%D1%81%D1%8B/%D0%BA%D0%B0%D1%82%D0%B0%D0%BB%D0%BE%D0%B3-%D0%BD%D0%BE%D0%B2%D0%BE%D1%81%D1%82%D1%80%D0%BE%D0%B5%D0%BA/%D0%BE%D0%B1%D1%8A%D0%B5%D0%BA%D1%82/58154", 
    "https://xn--80az8a.xn--d1aqf.xn--p1ai/%D1%81%D0%B5%D1%80%D0%B2%D0%B8%D1%81%D1%8B/%D0%B5%D0%B4%D0%B8%D0%BD%D1%8B%D0%B9-%D1%80%D0%B5%D0%B5%D1%81%D1%82%D1%80-%D0%B7%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D1%89%D0%B8%D0%BA%D0%BE%D0%B2/%D0%B7%D0%B0%D1%81%D1%82%D1%80%D0%BE%D0%B9%D1%89%D0%B8%D0%BA/17697" 
]

# ========== Функция парсинга сайта ==========
def parse_website(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Удаляем ненужные элементы
        for script in soup(["script", "style"]):
            script.extract()

        # Очищаем текст
        lines = (line.strip() for line in soup.get_text().splitlines())
        text = '\n'.join(line for line in lines if line)

        return text[:5000]  # Ограничиваем длину
    except Exception as e:
        print(f"[Ошибка] Не удалось спарсить {url}: {e}")
        return ""

# ========== Создание базы знаний ==========
def create_knowledge_base(urls):
    docs = []

    print("🔄 Начинаю парсинг сайтов...")
    for url in urls:
        print(f"🌐 Парсинг: {url}")
        content = parse_website(url)
        if content:
            docs.append({
                "text": content,
                "metadata": {"source": url}
            })

    print(f"📥 Спарсено документов: {len(docs)}")

    print("🧠 Загрузка модели эмбеддингов...")
    embeddings = HuggingFaceEmbeddings(model_name="all-mpnet-base-v2")#Более точная, но чуть медленнее
    #embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")#Быстрая и компактная, подходит для большинства задач
    #embeddings = HuggingFaceEmbeddings(model_name="multi-qa-mpnet-base-dot-v1")#Хорошо подходит для вопросно-ответных систем

    print("📚 Создание векторной базы знаний...")
    documents = [Document(page_content=d["text"], metadata=d["metadata"]) for d in docs]
    vectorstore = Chroma.from_documents(documents, embeddings, persist_directory=OUTPUT_DIR)
    vectorstore.persist()

    print(f"✅ Векторная база сохранена в папку: '{OUTPUT_DIR}'")

# ========== Точка входа ==========
if __name__ == "__main__":
    if os.path.exists(OUTPUT_DIR):
        print(f"⚠️ Папка '{OUTPUT_DIR}' уже существует. Удалите её, если хотите пересоздать.")
    else:
        create_knowledge_base(URLS)