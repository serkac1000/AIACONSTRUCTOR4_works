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

# Store API key temporarily in memory (not in session to avoid cookie issues)
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
        input[type="text"], input[type="password"], textarea, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
            box-sizing: border-box;
        }
        input[type="text"]:focus, input[type="password"]:focus, textarea:focus, select:focus {
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
        .btn-small {
            padding: 10px 20px;
            font-size: 14px;
            display: inline-block;
            margin: 10px 5px;
        }
        .btn-test {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
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
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
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
        .api-section {
            background: #e9ecef;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .api-status {
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
        }
        .status-connected {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
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
        <h1>🤖 MIT App Inventor AIA Generator</h1>

        <!-- Gemini API Configuration Section -->
        <div class="api-section">
            <h3>🔑 Gemini API Configuration</h3>
            <div class="form-group">
                <label for="geminiApiKey">Gemini API Key:</label>
                <input type="password" id="geminiApiKey" name="geminiApiKey" placeholder="Enter your Gemini API key">
                <small style="color: #666;">Get your API key from <a href="https://makersuite.google.com/app/apikey" target="_blank">Google AI Studio</a></small>
            </div>
            <button type="button" class="btn btn-small btn-test" onclick="testAndSaveGeminiAPI()">Test & Save API</button>
            <div id="apiStatus" class="api-status" style="display: none;"></div>
        </div>

        <form id="aiaForm">
            <div class="row">
                <div class="col">
                    <div class="form-group">
                        <label for="appName">App Name:</label>
                        <input type="text" id="appName" name="appName" required placeholder="MyApp">
                    </div>
                </div>
                <div class="col">
                    <div class="form-group">
                        <label for="appType">App Type:</label>
                        <select id="appType" name="appType">
                            <option value="basic">Basic App</option>
                            <option value="calculator">Calculator</option>
                            <option value="todo">Todo List</option>
                            <option value="game">Simple Game</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label for="prompt">Describe your app:</label>
                <textarea id="prompt" name="prompt" required placeholder="Create a simple calculator app with buttons for numbers 0-9, basic operations (+, -, *, /), equals button, and a display area."></textarea>
            </div>

            <div class="form-group">
                <label>
                    <input type="checkbox" id="useGemini" name="useGemini" checked> Use Gemini AI for enhanced generation
                </label>
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

        <div class="result error" id="errorResult">
            <h3>Error ❌</h3>
            <p id="errorMessage">Something went wrong...</p>
        </div>
    </div>

    <script>
        // Test and save Gemini API key
        async function testAndSaveGeminiAPI() {
            const apiKey = document.getElementById('geminiApiKey').value;
            if (!apiKey) {
                showAPIStatus('Please enter an API key first', 'error');
                return;
            }

            try {
                const response = await fetch('/test_gemini', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ api_key: apiKey })
                });

                const result = await response.json();
                if (result.success) {
                    showAPIStatus('✅ API key tested and saved successfully!', 'connected');
                    document.getElementById('geminiApiKey').value = ''; // Clear for security
                } else {
                    showAPIStatus('❌ API test failed: ' + result.error, 'error');
                }
            } catch (error) {
                showAPIStatus('❌ Network error: ' + error.message, 'error');
            }
        }

        function showAPIStatus(message, type) {
            const statusDiv = document.getElementById('apiStatus');
            statusDiv.textContent = message;
            statusDiv.className = 'api-status status-' + type;
            statusDiv.style.display = 'block';
        }

        // Form submission
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
                        // Error response
                        const errorData = await response.json();
                        showError('Generation failed: ' + errorData.error);
                    } else {
                        // Success - file download
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const filename = `${data.appName.replace(/[^a-z0-9]/gi, '_')}.aia`;

                        document.getElementById('downloadLink').href = url;
                        document.getElementById('downloadLink').download = filename;
                        document.getElementById('result').style.display = 'block';
                    }
                } else {
                    const errorText = await response.text();
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

def call_gemini_api(api_key, prompt):
    """Call Gemini API for app generation"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

        if prompt == "test":
            test_prompt = "Say hello"
        else:
            test_prompt = f"""Create a simple MIT App Inventor app specification for: {prompt}

            Respond with a basic JSON structure focusing on simple, working components."""

        payload = {
            "contents": [{
                "parts": [{
                    "text": test_prompt
                }]
            }]
        }

        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                return {"success": True, "content": content}
            else:
                return {"error": "No response from Gemini"}
        else:
            return {"error": f"API error: {response.status_code}"}

    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

def create_simple_project_structure(app_name, app_type, prompt):
    """Create simple, compatible MIT App Inventor project structure"""

    # Create simple components based on app type
    components = []

    if app_type == "calculator":
        # Simple calculator layout
        components.append({
            "$Name": "DisplayLabel",
            "$Type": "Label",
            "$Version": "4",
            "FontSize": "24",
            "Text": "0",
            "TextAlignment": "2",
            "BackgroundColor": "&HFFF0F0F0",
            "Width": "-2",
            "Height": "80",
            "Uuid": str(uuid.uuid4())
        })

        # Number buttons
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
    else:
        # Basic app components
        components.append({
            "$Name": "TitleLabel",
            "$Type": "Label",
            "$Version": "4",
            "FontSize": "20",
            "Text": f"Welcome to {app_name}",
            "TextAlignment": "1",
            "Width": "-2",
            "Height": "-1",
            "Uuid": str(uuid.uuid4())
        })

        components.append({
            "$Name": "ActionButton",
            "$Type": "Button",
            "$Version": "5",
            "Text": "Click Me",
            "FontSize": "16",
            "BackgroundColor": "&HFF4CAF50",
            "TextColor": "&HFFFFFFFF",
            "Width": "-2",
            "Height": "-1",
            "Uuid": str(uuid.uuid4())
        })

    # Use very basic, stable component versions
    project_properties = {
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

    return project_properties

def create_blocks_file():
    """Create proper blocks file structure"""
    return {
        "YaVersion": "208",
        "Source": "Form",
        "Properties": {
            "$Name": "Screen1",
            "$Type": "Form",
            "$Version": "25",
            "$Components": [],
            "$Blocks": {
                "Uuid": str(uuid.uuid4()),
                "collapse": "false",
                "comment": "",
                "disabled": "false",
                "type": "component_event",
                "x": "0",
                "y": "0"
            }
        }
    }

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/test_gemini', methods=['POST'])
def test_gemini():
    try:
        data = request.json
        api_key = data.get('api_key')

        if not api_key:
            return jsonify({'success': False, 'error': 'No API key provided'})

        # Test and store API key in memory
        result = call_gemini_api(api_key, "test")

        if result.get('success'):
            # Store API key temporarily
            api_key_storage['gemini_key'] = api_key
            return jsonify({'success': True, 'message': 'API key tested and saved'})
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Unknown error')})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate', methods=['POST'])
def generate_aia():
    try:
        data = request.json
        app_name = data.get('appName', 'MyApp')
        app_type = data.get('appType', 'basic')
        prompt = data.get('prompt', '')
        use_gemini = data.get('useGemini') == 'on'

        # Create simple project structure
        project_data = create_simple_project_structure(app_name, app_type, prompt)
        blocks_data = create_blocks_file()

        # Create AIA file
        aia_buffer = io.BytesIO()
        clean_app_name = app_name.replace(' ', '').replace('-', '').replace('_', '')

        with zipfile.ZipFile(aia_buffer, 'w', zipfile.ZIP_DEFLATED) as aia_file:
            # Add project.properties
            project_properties_content = f"""main=appinventor.ai_user.{clean_app_name}.Screen1
name={clean_app_name}
assets=../assets
source=../src
build=../build
versioncode=1
versionname=1.0
useslocation=false
aname={app_name}
sizing=Responsive"""
            aia_file.writestr('youngandroidproject/project.properties', project_properties_content)

            # Add Screen1.scm
            project_json = json.dumps(project_data, indent=2)
            screen_scm = f'#|\n$JSON\n{project_json}\n|#'
            aia_file.writestr(f'src/appinventor/ai_user/{clean_app_name}/Screen1.scm', screen_scm)

            # Add Screen1.bky (proper blocks XML format)
            blocks_xml = '''<xml xmlns="http://www.w3.org/1999/xhtml">
  <block type="component_event" id="1" x="0" y="0">
    <field name="component_object_name">Screen1</field>
    <field name="component_event_name">Initialize</field>
  </block>
</xml>'''
            aia_file.writestr(f'src/appinventor/ai_user/{clean_app_name}/Screen1.bky', blocks_xml)

            # Add required directories
            aia_file.writestr('assets/.gitkeep', '')
            aia_file.writestr('build/.gitkeep', '')
            aia_file.writestr('META-INF/MANIFEST.MF', 'Manifest-Version: 1.0\n')

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
    print("🚀 Starting MIT App Inventor AIA Generator...")
    print("📱 Server running at: http://0.0.0.0:5000")
    print("💡 Navigate to the URL above to start creating AIA files!")
    app.run(host='0.0.0.0', port=5000, debug=True)