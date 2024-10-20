import streamlit as st
import redis
from redis.commands.search.field import TextField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import os
import re
REDIS_END = os.environ['REDIS_ENDPOINT']
REDIS_PORT = os.environ['REDIS_PORT']
REDIS_PASSWORD = os.environ['REDIS_PASSWORD']

# Initialize Redis connection
r = redis.Redis(host=REDIS_END, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)

st.set_page_config(
    page_title="Search Index",
    page_icon="🤔",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Check if index exists and create it if it doesn't
def ensure_index_exists():
    try:
        # Check if the index already exists
        r.ft('idx:all').info()
        st.success("Index 'idx:all' already exists!")
    except redis.exceptions.ResponseError:
        # If the index doesn't exist, create it
        schema = (
            TextField("username", weight=5.0),
            TextField("handle", weight=5.0),
            TextField("content", weight=3.0),
            TextField("source", weight=1.0),
            TextField("title", weight=5.0),
            TextField("channel", weight=3.0),
            TextField("guild", weight=3.0),
            TextField("author", weight=5.0),
            TextField("message_link", weight=1.0)
        )

        r.ft('idx:all').create_index(
            schema,
            definition=IndexDefinition(
                prefix=['Tweet:', 'Spaces:', 'discord_message:'],
                index_type=IndexType.HASH
            )
        )
        st.success("Index 'idx:all' created successfully!")

    # Index/update existing documents
    index_documents()

    index_info = r.ft('idx:all').info()
    #st.json(index_info)

def index_documents():
    # Get all keys with the specified prefixes
    keys = r.keys('Tweet :*') + r.keys('Spaces :*') + r.keys('discord_message :*')
    
    indexed_count = 0
    for key in keys:
        # Get the document data
        doc = r.hgetall(key)
        
        # Update the document in Redis (this will also update the index)
        r.hset(key, mapping=doc)
        indexed_count += 1

    st.success(f"Indexed/Updated {indexed_count} documents")

ensure_index_exists()

# Streamlit UI
st.title("Creative Destruction XYZ Search")

# Search bar
query = st.text_input("Enter your search query:")

if query:
    # Construct a search query that looks for the terms in all indexed fields
    search_query = ' | '.join([f'@{field}:({query})' for field in [
        'username', 'handle', 'content', 'source', 'title', 'channel', 'guild', 'author', 'message_link'
    ]])

    try:
        results = r.ft('idx:all').search(Query(search_query).paging(0, 10).highlight().summarize())

        # Display results
        st.write(f"Found {results.total} results")
        st.text(f"Debug - Search query: {search_query}")
        st.text(f"Debug - Number of results: {len(results.docs)}")

        for doc in results.docs:
            # Determine the type of document
            if doc.id.startswith('Tweet:'):
                display_title = "Tweet"
                display_content = doc.content if hasattr(doc, 'content') else "No content"
            elif doc.id.startswith('Spaces:'):
                display_title = "Space"
                display_content = doc.title if hasattr(doc, 'title') else "No title"
            elif doc.id.startswith('discord_message:'):
                display_title = "Discord Message"
                display_content = doc.content if hasattr(doc, 'content') else "No content"
            else:
                display_title = "Unknown"
                display_content = "Unknown content"

                for key, value in doc.__dict__.items():
                    for field in ['username', 'handle', 'content', 'source', 'title', 'channel', 'guild', 'author', 'message_link']:
                        if key not in ['id', 'payload']:
                            st.text(f"{key}: {value}")
                        value1 = getattr(doc, field, "N/A")
                        st.text(f"{field}: {value1}")

    except redis.exceptions.ResponseError as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try a different search query.")

else:
    st.info("Enter a search query to see results.")

# Debug: Display a random document from Redis
random_key = r.randomkey()
if random_key:
    st.text("Random document from Redis:")
    st.json(r.hgetall(random_key))

st.text(f"Total keys in Redis: {r.dbsize()}")
st.text(f"Sample keys: {r.keys()[:5]}")