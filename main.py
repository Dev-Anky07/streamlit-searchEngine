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
        r.ft('idx:all').dropindex()
    except:
        pass

    schema = (
        # Tweet fields
        TextField("username", weight=5.0),
        TextField("handle", weight=5.0),
        TextField("content", weight=3.0),
        TextField("source", weight=1.0),
        # Spaces fields
        TextField("title", weight=5.0),
        # Discord fields
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
    index_info = r.ft('idx:all').info()
    st.json(index_info)

ensure_index_exists()

# Streamlit UI
st.title("Creative Destruction XYZ Search")

# Search bar
query = st.text_input("Enter your search query:")

if query:
    # Perform search
    search_query = f'({query})'

    try:
        results = r.ft('idx:all').search(Query(search_query).paging(0, 10).with_scores().return_fields("*"))

        # Display results
        st.write(f"Found {results.total} results")
        st.text(f"Debug - Search query: {search_query}")
        st.text(f"Debug - Number of results: {len(results.docs)}")

        for doc in results.docs:
            #st.text(f"Debug - Document ID: {doc.id}")
            #st.text(f"Debug - Document score: {doc.score}")

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

            with st.expander(f"{display_title}: {display_content[:100]}..."):
                for key, value in doc.__dict__.items():
                    if key not in ['id', 'payload']:
                        st.text(f"{key}: {value}")

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