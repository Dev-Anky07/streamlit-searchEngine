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

def escape_query(query):
    return re.sub(r'([&|!{}[\]^"~*?:\\()])', r'\\\1', query)

# Streamlit UI
st.title("Content Search Engine powered by Creative Destruction XYZ")

# Search bar
query = st.text_input("Enter your search query:")

if query:
    # Perform fuzzy search
    escaped_query = escape_query(query)
    search_query = f'*{escaped_query}*'

    try:
        # Debug: Print total number of documents in the index
        total_docs = r.ft('idx:all').info()['num_docs']
        st.text(f"Total documents in index: {total_docs}")

        results = r.ft('idx:all').search(Query(search_query).paging(0, 10).with_scores().no_content())

        # Display results
        st.write(f"Found {results.total} results")
        for doc in results.docs:
            # Fetch the full document from Redis
            full_doc = r.hgetall(doc.id)

            display_title = full_doc.get('username', full_doc.get('channel', 'Unknown'))
            display_content = full_doc.get('content', full_doc.get('title', full_doc.get('author', 'No content')))

            with st.expander(f"{display_title}: {display_content[:100]}..."):
                for key, value in full_doc.items():
                    st.text(f"{key}: {value}")

        # Pagination
        page = st.number_input("Page", min_value=1, max_value=(results.total // 10) + 1, value=1)
        if st.button("Load More"):
            offset = (page - 1) * 10
            results = r.ft('idx:all').search(Query(search_query).paging(offset, 10).with_scores().no_content())
            for doc in results.docs:
                full_doc = r.hgetall(doc.id)
                display_title = full_doc.get('username', full_doc.get('channel', 'Unknown'))
                display_content = full_doc.get('content', full_doc.get('title', full_doc.get('author', 'No content')))

                with st.expander(f"{display_title}: {display_content[:100]}..."):
                    for key, value in full_doc.items():
                        st.text(f"{key}: {value}")

    except redis.exceptions.ResponseError as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please try a different search query.")
        st.text(f"Debug - Search query: {search_query}")

    # Debug: Display a random document from the index
    random_key = r.randomkey()
    if random_key:
        st.text("Random document from index:")
        st.json(r.hgetall(random_key))

else:
    st.info("Enter a search query to see results.")