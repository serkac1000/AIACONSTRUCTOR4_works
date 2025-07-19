from flask import Flask, render_template, request, jsonify, send_file
import json
import zipfile
import io
import os
import uuid
from datetime import datetime

app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MIT App Inventor AIA Generator</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
        }
        input[type="text"], textarea, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
            box-sizing: border-box;
        }
        input[type="text"]:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea {
            height: 150px;
            resize: vertical;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            transition: transform 0.2s;
            display: block;
            margin: 20px auto;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            display: none;
        }
        .download-link {
            background: #28a745;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            display: inline-block;
            margin-top: 10px;
        }
        .row {
            display: flex;
            gap: 20px;
        }
        .col {
            flex: 1;
        }
        @media (max-width: 768px) {
            .row {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 MIT App Inventor AIA Generator</h1>
        <form id="aiaForm">
            <div class="row">
                <div class="col">
                    <div class="form-group">
                        <label for="appName">App Name:</label>
                        <input type="text" id="appName" name="appName" required placeholder="My Awesome App">
                    </div>
                </div>
                <div class="col">
                    <div class="form-group">
                        <label for="appType">App Type:</label>
                        <select id="appType" name="appType">
                            <option value="basic">Basic App</option>
                            <option value="game">Game</option>
                            <option value="utility">Utility</option>
                            <option value="educational">Educational</option>
                            <option value="social">Social</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div class="form-group">
                <label for="prompt">Describe your app (be specific about features, UI, and functionality):</label>
                <textarea id="prompt" name="prompt" required placeholder="Create a simple calculator app with buttons for numbers 0-9, basic operations (+, -, *, /), equals button, and clear button. The app should have a display screen showing the current number and result. Use a clean, modern design with blue buttons and white background."></textarea>
            </div>
            
            <button type="submit" class="btn">Generate AIA File</button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Generating your MIT App Inventor project...</p>
        </div>
        
        <div class="result" id="result">
            <h3>Success! 🎉</h3>
            <p>Your AIA file has been generated successfully.</p>
            <a href="#" class="download-link" id="downloadLink">Download AIA File</a>
        </div>
    </div>

    <script>
        document.getElementById('aiaForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            document.querySelector('.btn').disabled = true;
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const filename = `${data.appName.replace(/[^a-z0-9]/gi, '_')}.aia`;
                    
                    document.getElementById('downloadLink').href = url;
                    document.getElementById('downloadLink').download = filename;
                    document.getElementById('result').style.display = 'block';
                } else {
                    alert('Error generating AIA file. Please try again.');
                }
            } catch (error) {
                alert('Network error. Please check your connection and try again.');
            }
            
            document.getElementById('loading').style.display = 'none';
            document.querySelector('.btn').disabled = false;
        });
    </script>
</body>
</html>
'''

def create_basic_project_structure(app_name, app_type, prompt):
    """Create basic MIT App Inventor project structure based on prompt"""
    
    # Base project properties with proper MIT App Inventor format
    project_properties = {
        "YaVersion": "208",
        "Source": "Form",
        "Properties": {
            "$Name": "Screen1",
            "$Type": "Form",
            "$Version": "31",
            "AppName": app_name,
            "Title": app_name,
            "AboutScreen": "",
            "AlignHorizontal": "1",
            "AlignVertical": "1",
            "BackgroundColor": "&HFFFFFFFF",
            "BackgroundImage": "",
            "CloseScreenAnimation": "default",
            "Icon": "",
            "OpenScreenAnimation": "default",
            "ScreenOrientation": "portrait",
            "Scrollable": "False",
            "ShowListsAsJson": "True",
            "ShowStatusBar": "True",
            "Sizing": "Responsive",
            "Theme": "AppTheme.Light.DarkActionBar",
            "TitleVisible": "True",
            "VersionCode": "1",
            "VersionName": "1.0",
            "Uuid": str(uuid.uuid4())
        }
    }
    
    # Generate components based on app type and prompt
    components = []
    
    # Parse prompt for common UI elements
    prompt_lower = prompt.lower()
    
    if 'button' in prompt_lower:
        components.append({
            "$Name": "Button1",
            "$Type": "Button",
            "$Version": "7",
            "BackgroundColor": "&H007AFF",
            "FontBold": "True",
            "FontSize": "14",
            "Shape": "1",
            "Text": "Click Me",
            "TextColor": "&HFFFFFFFF",
            "Width": "-2",
            "Height": "-2",
            "Uuid": str(uuid.uuid4())
        })
    
    if 'label' in prompt_lower or 'text' in prompt_lower or 'display' in prompt_lower:
        components.append({
            "$Name": "Label1",
            "$Type": "Label",
            "$Version": "5",
            "FontSize": "14",
            "Text": "Hello World!",
            "TextAlignment": "1",
            "TextColor": "&HFF000000",
            "Width": "-2",
            "Height": "-2",
            "Uuid": str(uuid.uuid4())
        })
    
    if 'textbox' in prompt_lower or 'input' in prompt_lower:
        components.append({
            "$Name": "TextBox1",
            "$Type": "TextBox",
            "$Version": "5",
            "BackgroundColor": "&HFFFFFFFF",
            "FontSize": "14",
            "Hint": "Enter text here",
            "Width": "-2",
            "Height": "-2",
            "Uuid": str(uuid.uuid4())
        })
    
    if 'image' in prompt_lower:
        components.append({
            "$Name": "Image1",
            "$Type": "Image",
            "$Version": "4",
            "Width": "-2",
            "Height": "-2",
            "Uuid": str(uuid.uuid4())
        })
    
    if 'list' in prompt_lower:
        components.append({
            "$Name": "ListView1",
            "$Type": "ListView",
            "$Version": "6",
            "Width": "-2",
            "Height": "-2",
            "Uuid": str(uuid.uuid4())
        })
    
    # Add calculator-specific components if mentioned
    if 'calculator' in prompt_lower:
        # Add display label first
        components.append({
            "$Name": "DisplayLabel",
            "$Type": "Label",
            "$Version": "5",
            "BackgroundColor": "&HFFFFFFFF",
            "FontSize": "24",
            "Text": "0",
            "TextAlignment": "2",
            "TextColor": "&HFF000000",
            "Width": "-2",
            "Height": "-2",
            "Uuid": str(uuid.uuid4())
        })
        
        # Add number buttons
        for i in range(10):
            components.append({
                "$Name": f"Button{i}",
                "$Type": "Button",
                "$Version": "7",
                "BackgroundColor": "&HFF4CAF50",
                "FontBold": "True",
                "FontSize": "16",
                "Shape": "1",
                "Text": str(i),
                "TextColor": "&HFFFFFFFF",
                "Width": "-2",
                "Height": "-2",
                "Uuid": str(uuid.uuid4())
            })
        
        # Add operation buttons
        operations = ['+', '-', '*', '/', '=', 'C']
        for i, op in enumerate(operations):
            components.append({
                "$Name": f"ButtonOp{i}",
                "$Type": "Button",
                "$Version": "7",
                "BackgroundColor": "&HFFFF9800",
                "FontBold": "True",
                "FontSize": "16",
                "Shape": "1",
                "Text": op,
                "TextColor": "&HFFFFFFFF",
                "Width": "-2",
                "Height": "-2",
                "Uuid": str(uuid.uuid4())
            })
    
    # Add components to project
    if components:
        project_properties["Properties"]["$Components"] = components
    
    return project_properties

def create_blocks_file(app_name, components):
    """Create basic blocks file with simple event handlers"""
    blocks_data = {
        "YaVersion": "208",
        "Source": "Form",
        "Properties": {
            "$Name": "Screen1",
            "$Type": "Form", 
            "$Version": "31"
        }
    }
    
    # Create basic blocks structure - empty blocks file for now
    # MIT App Inventor will accept an empty blocks file
    blocks_data["blocks"] = {
        "languageVersion": 0,
        "blocks": []
    }
    
    return blocks_data

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/generate', methods=['POST'])
def generate_aia():
    try:
        data = request.json
        app_name = data.get('appName', 'MyApp')
        app_type = data.get('appType', 'basic')
        prompt = data.get('prompt', '')
        
        # Create project structure
        project_data = create_basic_project_structure(app_name, app_type, prompt)
        components = project_data["Properties"].get("$Components", [])
        
        # Create blocks data
        blocks_data = create_blocks_file(app_name, components)
        
        # Create AIA file in memory
        aia_buffer = io.BytesIO()
        
        # Clean app name for file paths
        clean_app_name = app_name.replace(' ', '').replace('-', '').replace('_', '')
        
        with zipfile.ZipFile(aia_buffer, 'w', zipfile.ZIP_DEFLATED) as aia_file:
            # Add project.properties with correct format
            project_properties_content = f"""main=appinventor.ai_user.{clean_app_name}.Screen1
name={clean_app_name}
assets=../assets
source=../src
build=../build
versioncode=1
versionname=1.0
useslocation=false
aname={app_name}
sizing=Responsive
showlistsasjson=true"""
            aia_file.writestr('youngandroidproject/project.properties', project_properties_content)
            
            # Add Screen1.scm (scheme file) with proper format
            project_json = json.dumps(project_data, indent=2)
            screen_scm = f'#|\n$JSON\n{project_json}\n|#'
            aia_file.writestr(f'src/appinventor/ai_user/{clean_app_name}/Screen1.scm', screen_scm)
            
            # Add Screen1.bky (blocks file) with proper format
            blocks_json = json.dumps(blocks_data, indent=2)
            blocks_content = f'#|\n$JSON\n{blocks_json}\n|#'
            aia_file.writestr(f'src/appinventor/ai_user/{clean_app_name}/Screen1.bky', blocks_content)
            
            # Add required directory structure
            aia_file.writestr('assets/.gitkeep', '')
            aia_file.writestr('build/.gitkeep', '')
            
            # Add meta-inf for proper AIA format
            aia_file.writestr('META-INF/MANIFEST.MF', 'Manifest-Version: 1.0\n')
        
        aia_buffer.seek(0)
        
        # Save a copy locally for debugging
        with open(f'{app_name.replace(" ", "_")}.aia', 'wb') as f:
            f.write(aia_buffer.getvalue())
        
        # Reset buffer position
        aia_buffer.seek(0)
        
        return send_file(
            aia_buffer,
            as_attachment=True,
            download_name=f'{app_name.replace(" ", "_")}.aia',
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting MIT App Inventor AIA Generator Server...")
    print("📱 Server running at: http://0.0.0.0:5000")
    print("💡 Navigate to the URL above to start creating AIA files!")
    app.run(host='0.0.0.0', port=5000, debug=True)