import os
import sys
import glob
import json
from dotenv import load_dotenv

# Add PageIndex library to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib', 'PageIndex'))

# Import PageIndex core functions
from pageindex import page_index_main, config

# Load environment variables
load_dotenv()

DATA_DIR = "lib/PageIndex/tests/pdfs"
INDEX_DIR = "lib/PageIndex/tests/results"

def process_pageindex():
    """
    Process PDF files using PageIndex to create hierarchical tree indices.
    """
    print("Starting PageIndex processing...")
    
    # Create output directory
    if not os.path.exists(INDEX_DIR):
        os.makedirs(INDEX_DIR)

    # Find all PDF files
    file_paths = glob.glob(os.path.join(DATA_DIR, "*.pdf"))
    
    if not file_paths:
        print(f"No PDF files found in {DATA_DIR}")
        print("Please place PDF files in lib/PageIndex/tests/pdfs/ or upload via the web interface")
        return

    # Configure PageIndex options
    model = os.getenv("OPENAI_MODEL", "gpt-4o-2024-11-20")  # PageIndex 預設用較強的模型
    opt = config(
        model=model,
        toc_check_page_num=20,
        max_page_num_each_node=10,
        max_token_num_each_node=12000,
        if_add_node_id='yes',
        if_add_node_summary='yes',
        if_add_doc_description='yes',
        if_add_node_text='no'
    )

    # Process each PDF
    for file_path in file_paths:
        print(f"\nProcessing {os.path.basename(file_path)}...")
        try:
            # Run PageIndex
            toc_with_page_number = page_index_main(file_path, opt)
            
            # Save the tree structure
            pdf_name = os.path.splitext(os.path.basename(file_path))[0]
            output_file = os.path.join(INDEX_DIR, f'{pdf_name}_structure.json')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(toc_with_page_number, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Successfully indexed: {pdf_name}")
            print(f"  Index saved to: {output_file}")
            
        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            import traceback
            traceback.print_exc()

    print("\nPageIndex processing complete.")

if __name__ == "__main__":
    process_pageindex()
