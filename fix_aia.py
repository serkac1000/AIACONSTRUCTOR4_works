import os 
import re 
import uuid 
 
print("=== DEBUG: Starting AIA fix script ===") 
 
# Read the original app.py file 
print("Reading app.py file...") 
with open('app.py', 'r', encoding='utf-8') as f: 
    content = f.read() 
 
print("Original app.py file loaded successfully") 
 
# Add debug print statements to the generate_aia function 
print("Adding debug print statements...") 
content = content.replace("def generate_aia():", "def generate_aia():\\n    print('=== DEBUG: Starting AIA generation ===')") 
 
# Replace the blocks file generation code 
print("Replacing blocks file generation code...") 
blocks_pattern = re.compile(r"(# Add proper blocks file with empty blocks workspace.*?)blocks_bky = '''#\|\n\$JSON\n.*?\|#'''", re.DOTALL) 
 
            # Create proper blocks with event handlers based on app type 
            if app_type == "calculator": 
$JSON 
{"YaVersion":"208","Source":"Form","Properties":{"$Name":"Screen1","$Type":"Form","$Version":"25","Uuid":"''' + str(uuid.uuid4()) + '''","Blocks":[ 
    {"type":"componentEvent","x":20,"y":20,"component_type":"Button","component_name":"ButtonEquals","event_name":"Click","is_generic":"false","collapsed":"false"}, 
    {"type":"componentEvent","x":20,"y":100,"component_type":"Button","component_name":"ButtonPlus","event_name":"Click","is_generic":"false","collapsed":"false"} 
]}} 
