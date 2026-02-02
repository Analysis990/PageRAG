import os
import sys
import json
import glob
from typing import Tuple, List
from dotenv import load_dotenv

# Add PageIndex library to path for utility functions
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib', 'PageIndex'))

from openai import OpenAI

load_dotenv()

INDEX_DIR = "data/pageindex_indices"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("CHATGPT_API_KEY")

async def query(message: str) -> Tuple[str, List[str]]:
    """
    Query the PageIndex system for specific documents.
    Uses the pre-built tree indices to navigate and find relevant content.
    """
    
    if not OPENAI_API_KEY:
        return "Error: OPENAI_API_KEY or CHATGPT_API_KEY not found.", []
    
    try:
        # Load all available tree indices
        index_files = glob.glob(os.path.join(INDEX_DIR, "*_structure.json"))
        
        if not index_files:
            return "No PageIndex indices found. Please run 'python scripts/process_pageindex.py' first to index your PDF documents.", []
        
        # Load indices
        indices = {}
        for index_file in index_files:
            doc_name = os.path.basename(index_file).replace("_structure.json", "")
            with open(index_file, 'r', encoding='utf-8') as f:
                indices[doc_name] = json.load(f)
        
        # Step 1: Determine which document(s) are most relevant
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        doc_descriptions = "\n".join([
            f"- {name}: {get_tree_summary(tree)}" 
            for name, tree in indices.items()
        ])
        
        doc_selection_prompt = f"""Given the following indexed documents and their descriptions:

{doc_descriptions}

User question: {message}

Which document(s) would be most relevant to answer this question? 
Respond with ONLY the document name(s), comma-separated if multiple."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": doc_selection_prompt}],
            temperature=0
        )
        
        selected_docs = response.choices[0].message.content.strip().split(',')
        selected_docs = [doc.strip() for doc in selected_docs if doc.strip() in indices]
        
        if not selected_docs:
            selected_docs = list(indices.keys())[:1]  # Fallback to first doc
        
        # Step 2: Navigate the tree structure to find relevant sections
        relevant_sections = []
        for doc_name in selected_docs:
            tree = indices[doc_name]
            sections = navigate_tree(tree, message, client, max_depth=3)
            relevant_sections.extend([(doc_name, section) for section in sections])
        
        if not relevant_sections:
            return f"I found the documents but couldn't locate relevant sections for your query in {', '.join(selected_docs)}.", selected_docs
        
        # Step 3: Generate answer based on relevant sections
        context = "\n\n".join([
            f"From {doc_name}, Section: {section.get('title', 'Untitled')}\n{section.get('summary', section.get('text', ''))}"
            for doc_name, section in relevant_sections[:3]  # Top 3 sections
        ])
        
        answer_prompt = f"""Based on the following excerpts from documents:

{context}

Please answer this question: {message}

Provide a clear and concise answer based on the information provided."""

        answer_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": answer_prompt}],
            temperature=0
        )
        
        answer = answer_response.choices[0].message.content
        
        return answer, [f"{doc}.pdf" for doc in selected_docs]
        
    except Exception as e:
        print(f"PageIndex Query Error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error processing PageIndex query: {str(e)}", []


def get_tree_summary(tree: dict) -> str:
    """Extract a summary from the tree structure."""
    if isinstance(tree, dict):
        if 'doc_description' in tree:
            return tree['doc_description']
        if 'title' in tree:
            return tree['title']
        if 'children' in tree and tree['children']:
            return f"Document with {len(tree['children'])} sections"
    return "Indexed document"


def navigate_tree(node: dict, query: str, client: OpenAI, current_depth: int = 0, max_depth: int = 3) -> List[dict]:
    """
    Recursively navigate the tree structure using LLM reasoning to find relevant sections.
    """
    if current_depth >= max_depth:
        return [node] if is_leaf_or_relevant(node) else []
    
    # If it's a leaf node, return it
    if 'children' not in node or not node['children']:
        return [node]
    
    # Use LLM to decide which children to explore
    children_summaries = []
    for i, child in enumerate(node['children']):
        title = child.get('title', f'Section {i+1}')
        summary = child.get('summary', child.get('node_id', ''))
        children_summaries.append(f"{i}: {title} - {summary}")
    
    navigation_prompt = f"""Given this query: "{query}"

The current section has the following subsections:
{chr(10).join(children_summaries)}

Which subsection(s) (by number) would be most relevant to explore? 
Respond with ONLY the numbers, comma-separated (e.g., "0,2" or "1"). Maximum 2 selections."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": navigation_prompt}],
            temperature=0
        )
        
        selected = response.choices[0].message.content.strip()
        indices = [int(x.strip()) for x in selected.split(',') if x.strip().isdigit()]
        indices = [i for i in indices if 0 <= i < len(node['children'])][:2]
        
    except:
        # Fallback: take first child
        indices = [0]
    
    # Recursively explore selected children
    results = []
    for idx in indices:
        results.extend(navigate_tree(node['children'][idx], query, client, current_depth + 1, max_depth))
    
    return results if results else [node]


def is_leaf_or_relevant(node: dict) -> bool:
    """Check if a node is a leaf or contains relevant content."""
    return 'text' in node or ('children' not in node or not node['children'])
