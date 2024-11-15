from MLbackend.src.devNetwork import communitySmellsDetector

def detect_community_smells(url, pat):
    senti_strength_path = Path(".", "MLbackend", "data")
    output_path = Path(".", "MLbackend", "src", "results")
    
    result = communitySmellsDetector(pat, url, senti_strength_path, output_path, LOGGER)
    
    if result:
        return result
    else:
        return None
