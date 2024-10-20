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
    st.json(index_info)

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
    # Perform search
    search_query = f'({query})'

    try:
        results = r.ft('idx:all').search(Query(search_query).paging(0, 10).with_scores().return_fields("*"))

        # Display results
        st.write(f"Found {results.total} results")
        st.text(f"Debug - Search query: {search_query}")
        st.text(f"Debug - Number of results: {len(results.docs)}")

        for doc in results.docs:
            st.text(f"Debug - Document ID: {doc.id}")
            st.text(f"Debug - Document score: {doc.score}")

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


'''
json data about the :

Index 'idx:all' created successfully!

{
"index_name":"idx:all"
"index_options":[]
"index_definition":[
0:"key_type"
1:"HASH"
2:"prefixes"
3:[
0:"Tweet:"
1:"Spaces:"
2:"discord_message:"
]
4:"default_score"
5:"1"
]
"attributes":[
0:[
0:"identifier"
1:"username"
2:"attribute"
3:"username"
4:"type"
5:"TEXT"
6:"WEIGHT"
7:"5"
]
1:[
0:"identifier"
1:"handle"
2:"attribute"
3:"handle"
4:"type"
5:"TEXT"
6:"WEIGHT"
7:"5"
]
2:[
0:"identifier"
1:"content"
2:"attribute"
3:"content"
4:"type"
5:"TEXT"
6:"WEIGHT"
7:"3"
]
3:[
0:"identifier"
1:"source"
2:"attribute"
3:"source"
4:"type"
5:"TEXT"
6:"WEIGHT"
7:"1"
]
4:[
0:"identifier"
1:"title"
2:"attribute"
3:"title"
4:"type"
5:"TEXT"
6:"WEIGHT"
7:"5"
]
5:[
0:"identifier"
1:"channel"
2:"attribute"
3:"channel"
4:"type"
5:"TEXT"
6:"WEIGHT"
7:"3"
]
6:[
0:"identifier"
1:"guild"
2:"attribute"
3:"guild"
4:"type"
5:"TEXT"
6:"WEIGHT"
7:"3"
]
7:[
0:"identifier"
1:"author"
2:"attribute"
3:"author"
4:"type"
5:"TEXT"
6:"WEIGHT"
7:"5"
]
8:[
0:"identifier"
1:"message_link"
2:"attribute"
3:"message_link"
4:"type"
5:"TEXT"
6:"WEIGHT"
7:"1"
]
]
"num_docs":"1"
"max_doc_id":"1"
"num_terms":"19"
"num_records":"19"
"inverted_sz_mb":"0.0018634796142578125"
"vector_index_sz_mb":"0"
"total_inverted_index_blocks":"19"
"offset_vectors_sz_mb":"1.811981201171875e-5"
"doc_table_size_mb":"9.822845458984375e-5"
"sortable_values_size_mb":"0"
"key_table_size_mb":"2.765655517578125e-5"
"tag_overhead_sz_mb":"0"
"text_overhead_sz_mb":"6.341934204101563e-4"
"total_index_memory_sz_mb":"0.0028104782104492188"
"geoshapes_sz_mb":"0"
"records_per_doc_avg":"19"
"bytes_per_record_avg":"102.84210205078125"
"offsets_per_term_avg":"1"
"offset_bits_per_record_avg":"8"
"hash_indexing_failures":"0"
"total_indexing_time":"0.08900000154972076"
"indexing":"0"
"percent_indexed":"1"
"number_of_uses":1
"cleaning":0
"gc_stats":[
0:"bytes_collected"
1:"0"
2:"total_ms_run"
3:"0"
4:"total_cycles"
5:"0"
6:"average_cycle_time_ms"
7:"nan"
8:"last_run_time_ms"
9:"0"
10:"gc_numeric_trees_missed"
11:"0"
12:"gc_blocks_denied"
13:"0"
]
"cursor_stats":[
0:"global_idle"
1:0
2:"global_total"
3:0
4:"index_capacity"
5:128
6:"index_total"
7:0
]
"dialect_stats":[
0:"dialect_1"
1:0
2:"dialect_2"
3:0
4:"dialect_3"
5:0
6:"dialect_4"
7:0
]
"Index Errors":[
0:"indexing failures"
1:0
2:"last indexing error"
3:"N/A"
4:"last indexing error key"
5:"N/A"
]
"field statistics":[
0:[
0:"identifier"
1:"username"
2:"attribute"
3:"username"
4:"Index Errors"
5:[
0:"indexing failures"
1:0
2:"last indexing error"
3:"N/A"
4:"last indexing error key"
5:"N/A"
]
]
1:[
0:"identifier"
1:"handle"
2:"attribute"
3:"handle"
4:"Index Errors"
5:[
0:"indexing failures"
1:0
2:"last indexing error"
3:"N/A"
4:"last indexing error key"
5:"N/A"
]
]
2:[
0:"identifier"
1:"content"
2:"attribute"
3:"content"
4:"Index Errors"
5:[
0:"indexing failures"
1:0
2:"last indexing error"
3:"N/A"
4:"last indexing error key"
5:"N/A"
]
]
3:[
0:"identifier"
1:"source"
2:"attribute"
3:"source"
4:"Index Errors"
5:[
0:"indexing failures"
1:0
2:"last indexing error"
3:"N/A"
4:"last indexing error key"
5:"N/A"
]
]
4:[
0:"identifier"
1:"title"
2:"attribute"
3:"title"
4:"Index Errors"
5:[
0:"indexing failures"
1:0
2:"last indexing error"
3:"N/A"
4:"last indexing error key"
5:"N/A"
]
]
5:[
0:"identifier"
1:"channel"
2:"attribute"
3:"channel"
4:"Index Errors"
5:[
0:"indexing failures"
1:0
2:"last indexing error"
3:"N/A"
4:"last indexing error key"
5:"N/A"
]
]
6:[
0:"identifier"
1:"guild"
2:"attribute"
3:"guild"
4:"Index Errors"
5:[
0:"indexing failures"
1:0
2:"last indexing error"
3:"N/A"
4:"last indexing error key"
5:"N/A"
]
]
7:[
0:"identifier"
1:"author"
2:"attribute"
3:"author"
4:"Index Errors"
5:[
0:"indexing failures"
1:0
2:"last indexing error"
3:"N/A"
4:"last indexing error key"
5:"N/A"
]
]
8:[
0:"identifier"
1:"message_link"
2:"attribute"
3:"message_link"
4:"Index Errors"
5:[
0:"indexing failures"
1:0
2:"last indexing error"
3:"N/A"
4:"last indexing error key"
5:"N/A"
]
]
]
}
'''