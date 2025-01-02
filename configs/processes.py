from math import floor
import os
import re
import google.generativeai as genai
import numpy as np
from .tasks import *
from .agents import *
import logging
logger = logging.getLogger(__name__)
logger.propagate = True


def is_valid_vector(vector):
    """Validate that a vector contains only finite float values."""
    return (isinstance(vector, (list, np.ndarray)) and 
            all(isinstance(x, float) and np.isfinite(x) for x in vector))


def get_valid_embedding(model, content, task_type, max_attempts=10):
    """Get a valid embedding with retry logic."""
    for attempt in range(max_attempts):
        try:
            embedding = genai.embed_content(
                model=model,
                content=content,
                task_type=task_type
            )['embedding']
            
            if is_valid_vector(embedding):
                return embedding
                
            logger.warning(f"Invalid embedding received, attempt {attempt + 1}/{max_attempts}")
        except Exception as e:
            logger.warning(f"Embedding error on attempt {attempt + 1}/{max_attempts}: {str(e)}")
            
    raise ValueError(f"Failed to get valid embedding after {max_attempts} attempts")


def fetch_relevant_code(data, query, num_results=5):
    """Fetch relevant code segments based on semantic similarity to query.
    
    Args:
        data: Dictionary containing 'code_segment' list
        query: String to compare against code segments
        num_results: Number of top results to return
        
    Returns:
        List of segment_content strings from most similar code segments
    """
    try:
        # Configure Google API
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        model = "models/embedding-001"
        
        # Get query embedding with validation
        query_embedding = get_valid_embedding(model, query, "retrieval_query")
        
        # Process each code segment
        similarities = []
        for item in data['code_segments']:
            # Get or create embedding for segment
            if 'vector' not in item or not item['vector']:
                item['vector'] = get_valid_embedding(
                    model,
                    item['segment_description'],
                    "retrieval_document"
                )
            
            # Calculate cosine similarity
            vector = np.array(item['vector'])
            query_vec = np.array(query_embedding)
            cosine_sim = np.dot(vector, query_vec) / (np.linalg.norm(vector) * np.linalg.norm(query_vec))
            similarities.append((cosine_sim, item))
        
        # Sort by similarity and return top results
        similarities.sort(reverse=True, key=lambda x: x[0])
        return [item['segment_content'] for _, item in similarities[:num_results]]
        
    except Exception as e:
        logger.error(f"Error in fetch_relevant_code: {str(e)}")
        return []


# Used to run validation via tasks with a list of items and a validation target
def validate_items(
        data, 
        validation_task,
        input_label,
        validation_target,
        output_label,
        n=5
):
    
    # For tracking items that pass/fail validation
    new_data = {
        output_label: {
            'pass': [],
            'fail': []
        }
    }
    
    number_of_items = len(data[input_label])
    if number_of_items <= n:
        i_max = 0
    else:
        i_partition = floor(number_of_items / n)
        i_max = i_partition * n
        for i in range(0, i_partition, n):
            data_slice = data[input_label][i:i+n]
            new_data[output_label]['pass'] += product_owner.perform_task(
                validation_task, 
                inputs={
                    input_label: data_slice,
                    validation_target: json.dumps(
                        {validation_target: data[validation_target]}, 
                        indent=4
                    )
                }
            )[output_label]

            # Seperate out items that fail validation
            for i, item in enumerate(new_data[output_label]['pass']):
                if item['requirement_implemented'].lower() not in ['pass', 'yes', 'true']:
                    failed_item = new_data[output_label]['pass'].pop(i)
                    new_data[output_label]['fail'].append(failed_item)

    # Validate remaining requirements
    data_slice = input_label[input_label][i_max:]
    new_data[output_label]['pass'] = product_owner.perform_task(
        validate_code, 
        inputs={
            input_label: data_slice,
            validation_target: json.dumps(
                {validation_target: data[validation_target]}, 
                indent=4
            )
        }
    )[output_label]

    # Seperate out items that fail validation
    for i, item in enumerate(new_data[output_label]['pass']):
        if item['is_complete'].lower() not in ['pass', 'yes', 'true']:
            failed_item = new_data[output_label]['pass'].pop(i)
            new_data[output_label]['fail'].append(failed_item)

    return new_data


# Compares 2 different code content values with all formatting removed
def calculate_diff(c1, c2):
    # Clean both strings by removing whitespace, newlines, punctuation and converting to lowercase
    def clean_string(s):
        # Remove code block markers
        s = re.sub('\`\`\`[a-zA-Z0-9]*', '', s)
        # Convert to lowercase
        s = s.lower()
        # Remove all whitespace and newlines
        s = re.sub(r'\s+', '', s)
        # Remove all punctuation except for meaningful code characters
        s = re.sub(r'[^\w\s]', '', s)
        return s

    # Clean both strings
    clean1 = clean_string(c1)
    clean2 = clean_string(c2)

    # If strings are identical after cleaning, return None
    if clean1 == clean2:
        return None

    # Create colored diff output for original strings
    diff = list(ndiff(clean2.splitlines(True), clean1.splitlines(True)))
    
    result = []
    for line in diff:
        if line.startswith('+ '):
            result.append(f"\033[32m{line}\033[0m")  # Green for additions
        elif line.startswith('- '):
            result.append(f"\033[31m{line}\033[0m")  # Red for deletions
        elif line.startswith('? '):
            continue
        else:
            result.append(line)
    
    return result if result else None


# LEGACY: Uses the LLM to generate semantic descriptions for sections of code in order to do better RAG later...
def index_code(code_gen_data, max_attempts = 3):

    files = {'files': code_gen_data['files']}

    for i in range(max_attempts):
        data = developer.perform_task(
            index_code_semantically,
            inputs={
                'source_files': json.dumps(files, indent=4)
            }
        )

        # To validate Code Indexing, ensure all chunks in each file add up to same content as original file
        parsed_files = {}
        for seg in data['code_segments']:
            k = seg['file_name']
            parsed_files[k] = parsed_files.get(k, "") + seg['segment_content']

        # For each file, validate that the process completed successfully
        for f in files['files']:
            c1 = parsed_files[f['file_name']]
            c2 = f['file_content']
            diffs = calculate_diff(c1, c2)
            if not diffs:
                logger.debug(f"Code segments add up cleanly to original source data \"{f['file_name']}\". Segmentation successful!")
                data = code_gen_data | data
                return data
            else:
                logger.debug(f"Found differences in segmenting source code \"{f['file_name']}\"... See below:")
                for line in diffs:
                    print(line)
                logger.debug(f"Trying again...")
    return False
