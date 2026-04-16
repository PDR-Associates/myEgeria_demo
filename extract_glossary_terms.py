import re

def extract_glossary_terms(text):
    """
    Extracts GlossaryTerm items from a string structure.
    Each item starts with 'GlossaryTerm::' and ends at the next ','.
    """
    # Pattern: GlossaryTerm:: followed by anything that is NOT a comma, 
    # capturing the part after the ::
    pattern = r"GlossaryTerm::([^,]+)"
    
    # Find all matches
    matches = re.findall(pattern, text)
    
    # Return stripped items
    return [match.strip() for match in matches]

if __name__ == "__main__":
    # Sample structure based on user description
    sample_data = "Folder: Main, GlossaryTerm:: Term A, GlossaryTerm::Term B , Folder: Sub, GlossaryTerm:: Term C,"
    
    print(f"Input string: {sample_data}")
    terms = extract_glossary_terms(sample_data)
    print(f"Extracted terms: {terms}")

    # Example with more realistic metadata string if applicable
    sample_metadata = "Entity: {qualifiedName: GlossaryTerm::Customer Segment, type: GlossaryTerm}, Entity: {qualifiedName: GlossaryTerm::Revenue Type, type: GlossaryTerm},"
    print(f"\nMetadata input: {sample_metadata}")
    metadata_terms = extract_glossary_terms(sample_metadata)
    print(f"Extracted metadata terms: {metadata_terms}")
