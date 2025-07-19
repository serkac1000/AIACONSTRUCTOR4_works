
from flask import Flask, render_template, request, jsonify, send_file
import json
import zipfile
import io
import os
import uuid
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Store API key temporarily in memory
api_key_storage = {}

# HTML template for the web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MIT App Inventor AIA Generator</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
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
        input, textarea, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea {
            height: 120px;
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
            width: 100%;
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
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            display: none;
            text-align: center;
        }
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .download-link {
            background: #28a745;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            display: inline-block;
            margin-top: 15px;
            font-weight: bold;
        }
        .info-box {
            background: #e9ecef;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .info-box h3 {
            color: #495057;
            margin-bottom: 10px;
        }
        .info-box p {
            color: #6c757d;
            line-height: 1.5;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 MIT App Inventor AIA Generator</h1>
        
        <div class="info-box">
            <h3>📱 How to Test Your App</h3>
            <p>1. Download the generated AIA file<br>
            2. Go to <a href="https://appinventor.mit.edu" target="_blank">MIT App Inventor</a><br>
            3. Import the AIA file using "Projects → Import project (.aia)"<br>
            4. Use MIT AI2 Companion app to test on your phone</p>
        </div>

        <form id="aiaForm">
            <div class="form-group">
                <label for="appName">App Name:</label>
                <input type="text" id="appName" name="appName" required placeholder="MyAwesomeApp" value="TestApp">
            </div>

            <div class="form-group">
                <label for="appType">App Type:</label>
                <select id="appType" name="appType">
                    <option value="basic">Basic App</option>
                    <option value="calculator">Calculator</option>
                    <option value="counter">Counter App</option>
                    <option value="clicker">Button Clicker</option>
                </select>
            </div>

            <div class="form-group">
                <label for="prompt">Describe your app:</label>
                <textarea id="prompt" name="prompt" required placeholder="Create a simple app with buttons and labels">Create a simple app with a welcome message and interactive buttons</textarea>
            </div>

            <button type="submit" class="btn">Generate AIA File</button>
        </form>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Generating your MIT App Inventor project...</p>
        </div>

        <div class="result" id="result">
            <h3>✅ Success!</h3>
            <p>Your AIA file has been generated and is ready to import into MIT App Inventor.</p>
            <a href="#" class="download-link" id="downloadLink">Download AIA File</a>
        </div>

        <div class="result error" id="errorResult">
            <h3>❌ Error</h3>
            <p id="errorMessage">Something went wrong...</p>
        </div>
    </div>

    <script>
        document.getElementById('aiaForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);

            document.getElementById('loading').style.display = 'block';
            document.getElementById('result').style.display = 'none';
            document.getElementById('errorResult').style.display = 'none';
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
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        const errorData = await response.json();
                        showError('Generation failed: ' + errorData.error);
                    } else {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const filename = `${data.appName.replace(/[^a-z0-9]/gi, '_')}.aia`;

                        document.getElementById('downloadLink').href = url;
                        document.getElementById('downloadLink').download = filename;
                        document.getElementById('result').style.display = 'block';
                    }
                } else {
                    showError('Server error: ' + response.status);
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            }

            document.getElementById('loading').style.display = 'none';
            document.querySelector('.btn').disabled = false;
        });

        function showError(message) {
            document.getElementById('errorMessage').textContent = message;
            document.getElementById('errorResult').style.display = 'block';
        }
    </script>
</body>
</html>
'''

def create_project_structure(app_name, app_type, prompt):
    """Create MIT App Inventor compatible project structure"""
    
    components = []
    
    # Create components based on app type
    if app_type == "calculator":
        # Display label
        components.append({
            "$Name": "DisplayLabel",
            "$Type": "Label",
            "$Version": "4",
            "FontSize": "24",
            "Text": "0",
            "TextAlignment": "2",
            "BackgroundColor": "&HFFF5F5F5",
            "Width": "-2",
            "Height": "80",
            "Uuid": str(uuid.uuid4())
        })
        
        # Number buttons 0-9
        for i in range(10):
            components.append({
                "$Name": f"Button{i}",
                "$Type": "Button",
                "$Version": "5",
                "Text": str(i),
                "FontSize": "18",
                "Width": "80",
                "Height": "60",
                "Uuid": str(uuid.uuid4())
            })
            
        # Operation buttons
        for op, name in [("+", "Plus"), ("-", "Minus"), ("*", "Multiply"), ("/", "Divide"), ("=", "Equals")]:
            components.append({
                "$Name": f"Button{name}",
                "$Type": "Button",
                "$Version": "5",
                "Text": op,
                "FontSize": "18",
                "Width": "80",
                "Height": "60",
                "BackgroundColor": "&HFFFFA500",
                "Uuid": str(uuid.uuid4())
            })
            
    elif app_type == "counter":
        # Counter display
        components.append({
            "$Name": "CounterLabel",
            "$Type": "Label",
            "$Version": "4",
            "FontSize": "36",
            "Text": "0",
            "TextAlignment": "1",
            "Width": "-2",
            "Height": "100",
            "BackgroundColor": "&HFFF0F0F0",
            "Uuid": str(uuid.uuid4())
        })
        
        # Increment button
        components.append({
            "$Name": "IncrementButton",
            "$Type": "Button",
            "$Version": "5",
            "Text": "+1",
            "FontSize": "20",
            "BackgroundColor": "&HFF4CAF50",
            "TextColor": "&HFFFFFFFF",
            "Width": "120",
            "Height": "60",
            "Uuid": str(uuid.uuid4())
        })
        
        # Decrement button
        components.append({
            "$Name": "DecrementButton",
            "$Type": "Button",
            "$Version": "5",
            "Text": "-1",
            "FontSize": "20",
            "BackgroundColor": "&HFFF44336",
            "TextColor": "&HFFFFFFFF",
            "Width": "120",
            "Height": "60",
            "Uuid": str(uuid.uuid4())
        })
        
        # Reset button
        components.append({
            "$Name": "ResetButton",
            "$Type": "Button",
            "$Version": "5",
            "Text": "Reset",
            "FontSize": "16",
            "BackgroundColor": "&HFF9E9E9E",
            "Width": "120",
            "Height": "50",
            "Uuid": str(uuid.uuid4())
        })
        
    elif app_type == "clicker":
        # Score display
        components.append({
            "$Name": "ScoreLabel",
            "$Type": "Label",
            "$Version": "4",
            "FontSize": "24",
            "Text": "Score: 0",
            "TextAlignment": "1",
            "Width": "-2",
            "Height": "60",
            "Uuid": str(uuid.uuid4())
        })
        
        # Click button
        components.append({
            "$Name": "ClickButton",
            "$Type": "Button",
            "$Version": "5",
            "Text": "Click Me!",
            "FontSize": "20",
            "BackgroundColor": "&HFF2196F3",
            "TextColor": "&HFFFFFFFF",
            "Width": "200",
            "Height": "100",
            "Uuid": str(uuid.uuid4())
        })
        
    else:  # basic app
        # Welcome label
        components.append({
            "$Name": "WelcomeLabel",
            "$Type": "Label",
            "$Version": "4",
            "FontSize": "20",
            "Text": f"Welcome to {app_name}!",
            "TextAlignment": "1",
            "Width": "-2",
            "Height": "80",
            "Uuid": str(uuid.uuid4())
        })
        
        # Action button
        components.append({
            "$Name": "ActionButton",
            "$Type": "Button",
            "$Version": "5",
            "Text": "Click Me",
            "FontSize": "18",
            "BackgroundColor": "&HFF4CAF50",
            "TextColor": "&HFFFFFFFF",
            "Width": "-2",
            "Height": "60",
            "Uuid": str(uuid.uuid4())
        })
        
        # Status label
        components.append({
            "$Name": "StatusLabel",
            "$Type": "Label",
            "$Version": "4",
            "FontSize": "16",
            "Text": "Ready",
            "TextAlignment": "1",
            "Width": "-2",
            "Height": "40",
            "BackgroundColor": "&HFFF5F5F5",
            "Uuid": str(uuid.uuid4())
        })

    # Create the main project structure
    project_data = {
        "YaVersion": "208",
        "Source": "Form",
        "Properties": {
            "$Name": "Screen1",
            "$Type": "Form",
            "$Version": "25",
            "AppName": app_name,
            "Title": app_name,
            "AlignHorizontal": "1",
            "AlignVertical": "1",
            "BackgroundColor": "&HFFFFFFFF",
            "ScreenOrientation": "portrait",
            "Scrollable": "False",
            "TitleVisible": "True",
            "VersionCode": "1",
            "VersionName": "1.0",
            "Uuid": str(uuid.uuid4()),
            "$Components": components
        }
    }
    
    return project_data

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/generate', methods=['POST'])
def generate_aia():
    try:
        data = request.json
        app_name = data.get('appName', 'MyApp').strip()
        app_type = data.get('appType', 'basic')
        prompt = data.get('prompt', '').strip()

        # Validate inputs
        if not app_name:
            return jsonify({'error': 'App name is required'}), 400

        # Clean app name for file system
        clean_app_name = ''.join(c for c in app_name if c.isalnum())
        if not clean_app_name:
            clean_app_name = 'MyApp'

        # Create project structure
        project_data = create_project_structure(app_name, app_type, prompt)

        # Create AIA file
        aia_buffer = io.BytesIO()

        with zipfile.ZipFile(aia_buffer, 'w', zipfile.ZIP_DEFLATED) as aia_file:
            # Add project.properties with correct format
            project_properties = f"""main=appinventor.ai_user.{clean_app_name}.Screen1
name={clean_app_name}
assets=../assets
source=../src
build=../build
versioncode=1
versionname=1.0
useslocation=false
aname={app_name}
sizing=Responsive
actionbar=false"""
            aia_file.writestr('youngandroidproject/project.properties', project_properties)

            # Add Screen1.scm with proper format
            project_json = json.dumps(project_data, indent=2)
            screen_scm = f'#|\n$JSON\n{project_json}\n|#'
            aia_file.writestr(f'src/appinventor/ai_user/{clean_app_name}/Screen1.scm', screen_scm)

            # Add proper blocks file - simpler format that MIT AI2 expects
            blocks_bky = f'''#|
$JSON
{{"YaVersion":"208","Source":"Form","Properties":{{"$Name":"Screen1","$Type":"Form","$Version":"25","Uuid":"{str(uuid.uuid4())}"}}}}
|#'''
            aia_file.writestr(f'src/appinventor/ai_user/{clean_app_name}/Screen1.bky', blocks_bky)

            # Add required empty directories
            aia_file.writestr('assets/', '')
            aia_file.writestr('build/', '')
            
            # Add proper manifest
            manifest = """Manifest-Version: 1.0
Created-By: MIT App Inventor

"""
            aia_file.writestr('META-INF/MANIFEST.MF', manifest)

        aia_buffer.seek(0)

        return send_file(
            aia_buffer,
            as_attachment=True,
            download_name=f'{clean_app_name}.aia',
            mimetype='application/zip'
        )

    except Exception as e:
        print(f"Error generating AIA: {str(e)}")
        return jsonify({'error': f'Generation failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 Starting MIT App Inventor AIA Generator...")
    print("📱 Server running at: http://0.0.0.0:5000")
    print("💡 Navigate to the URL above to start creating AIA files!")
    app.run(host='0.0.0.0', port=5000, debug=True)
