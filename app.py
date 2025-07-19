
from flask import Flask, render_template, request, jsonify, send_file, session
import json
import zipfile
import io
import os
import uuid
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# HTML template for the web interface with Gemini API integration
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MIT App Inventor AIA Generator with Gemini AI</title>
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
        <h1>🤖 MIT App Inventor AIA Generator with Gemini AI</h1>
        
        <!-- Gemini API Configuration Section -->
        <div class="api-section">
            <h3>🔑 Gemini API Configuration</h3>
            <div class="form-group">
                <label for="geminiApiKey">Gemini API Key:</label>
                <input type="password" id="geminiApiKey" name="geminiApiKey" placeholder="Enter your Gemini API key">
                <small style="color: #666;">Get your API key from <a href="https://makersuite.google.com/app/apikey" target="_blank">Google AI Studio</a></small>
            </div>
            <button type="button" class="btn btn-small btn-test" onclick="testGeminiAPI()">Test API</button>
            <button type="button" class="btn btn-small" onclick="saveGeminiAPI()">Save API Key</button>
            <div id="apiStatus" class="api-status" style="display: none;"></div>
        </div>

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
                            <option value="calculator">Calculator</option>
                            <option value="todo">Todo List</option>
                            <option value="weather">Weather App</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div class="form-group">
                <label for="prompt">Describe your app (be very specific about features, UI layout, colors, and functionality):</label>
                <textarea id="prompt" name="prompt" required placeholder="Create a calculator app with a display screen at the top, number buttons (0-9) arranged in a 4x3 grid, operation buttons (+, -, *, /) on the right side, an equals button at the bottom, and a clear button. Use blue buttons with white text, white background, and make the display show large black text. The app should handle basic arithmetic operations and show results when equals is pressed."></textarea>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="useGemini" name="useGemini" checked> Use Gemini AI for enhanced generation
                </label>
            </div>
            
            <button type="submit" class="btn">Generate AIA File with AI</button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Generating your MIT App Inventor project with AI...</p>
        </div>
        
        <div class="result" id="result">
            <h3>Success! 🎉</h3>
            <p>Your AIA file has been generated successfully.</p>
            <a href="#" class="download-link" id="downloadLink">Download AIA File</a>
        </div>

        <div class="result error" id="errorResult">
            <h3>Error ❌</h3>
            <p id="errorMessage">Something went wrong...</p>
            <details>
                <summary>Technical Details</summary>
                <pre id="errorDetails"></pre>
            </details>
        </div>
    </div>

    <script>
        let apiKeyStored = false;

        // Test Gemini API connection
        async function testGeminiAPI() {
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
                    showAPIStatus('✅ API connection successful!', 'connected');
                } else {
                    showAPIStatus('❌ API test failed: ' + result.error, 'error');
                }
            } catch (error) {
                showAPIStatus('❌ Network error: ' + error.message, 'error');
            }
        }

        // Save Gemini API key
        async function saveGeminiAPI() {
            const apiKey = document.getElementById('geminiApiKey').value;
            if (!apiKey) {
                showAPIStatus('Please enter an API key first', 'error');
                return;
            }

            try {
                const response = await fetch('/save_gemini_key', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ api_key: apiKey })
                });
                
                const result = await response.json();
                if (result.success) {
                    showAPIStatus('✅ API key saved successfully!', 'connected');
                    apiKeyStored = true;
                    document.getElementById('geminiApiKey').value = ''; // Clear for security
                } else {
                    showAPIStatus('❌ Failed to save API key: ' + result.error, 'error');
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
                        showError('Generation failed: ' + errorData.error, errorData.details || '');
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
                    showError('Server error: ' + response.status, errorText);
                }
            } catch (error) {
                showError('Network error: ' + error.message, 'Check your internet connection and try again.');
            }
            
            document.getElementById('loading').style.display = 'none';
            document.querySelector('.btn').disabled = false;
        });

        function showError(message, details) {
            document.getElementById('errorMessage').textContent = message;
            document.getElementById('errorDetails').textContent = details;
            document.getElementById('errorResult').style.display = 'block';
        }
    </script>
</body>
</html>
'''

def call_gemini_api(api_key, prompt):
    """Call Gemini API to enhance app generation"""
    try:
        # Clean the API key
        api_key = api_key.strip()
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        # For testing, use a simple prompt
        if prompt == "Say hello":
            test_prompt = "Say hello world"
        else:
            test_prompt = f"""
            You are an expert MIT App Inventor developer. Based on the following app description, generate a detailed specification for creating an AIA file.

            App Description: {prompt}

            Please provide a JSON response with the following structure:
            {{
                "components": [
                    {{
                        "name": "component_name",
                        "type": "Button|Label|TextBox|Image|ListView|etc",
                        "properties": {{
                            "Text": "button text",
                            "BackgroundColor": "#FF4CAF50",
                            "TextColor": "#FFFFFF",
                            "FontSize": "16",
                            "Width": "-2",
                            "Height": "-2"
                        }}
                    }}
                ],
                "layout": {{
                    "arrangement": "vertical|horizontal",
                    "background_color": "#FFFFFF",
                    "title": "App Title"
                }},
                "blocks": [
                    {{
                        "component": "Button1",
                        "event": "Click",
                        "action": "set_text_to_label"
                    }}
                ]
            }}

            Focus on creating a functional, well-designed app with proper component arrangement and styling.
            """
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": test_prompt
                }]
            }]
        }
        
        print(f"Making request to: {url[:80]}...")  # Debug log (partial URL)
        print(f"Payload: {json.dumps(payload, indent=2)[:200]}...")  # Debug log (partial payload)
        
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")  # Debug log
        print(f"Response headers: {dict(response.headers)}")  # Debug log
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response content: {json.dumps(result, indent=2)[:500]}...")  # Debug log
            
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['parts'][0]['text']
                
                # For test requests, just return success
                if prompt == "Say hello":
                    return {"success": True, "message": content}
                
                # Try to extract JSON from the response for actual requests
                try:
                    # Look for JSON content between ```json and ``` or just parse directly
                    if '```json' in content:
                        json_start = content.find('```json') + 7
                        json_end = content.find('```', json_start)
                        json_content = content[json_start:json_end].strip()
                    elif '{' in content and '}' in content:
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        json_content = content[json_start:json_end]
                    else:
                        json_content = content
                    
                    return json.loads(json_content)
                except json.JSONDecodeError:
                    # If JSON parsing fails, return a basic structure
                    return {
                        "components": [],
                        "layout": {"arrangement": "vertical", "background_color": "#FFFFFF"},
                        "blocks": [],
                        "ai_response": content  # Include raw response for debugging
                    }
            else:
                return {"error": "No response candidates from Gemini"}
        else:
            error_text = response.text
            print(f"API Error Response: {error_text}")  # Debug log
            return {"error": f"API call failed: {response.status_code} - {error_text}"}
            
    except requests.exceptions.Timeout:
        return {"error": "API request timed out"}
    except requests.exceptions.ConnectionError:
        return {"error": "Failed to connect to Gemini API"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error in call_gemini_api: {str(e)}")  # Debug log
        return {"error": f"Unexpected error: {str(e)}"}

def create_advanced_project_structure(app_name, app_type, prompt, gemini_data=None):
    """Create advanced MIT App Inventor project structure using Gemini AI data"""
    
    # Base project properties
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
    
    # Apply Gemini-generated layout if available
    if gemini_data and 'layout' in gemini_data:
        layout = gemini_data['layout']
        if 'background_color' in layout:
            try:
                # Convert hex color to MIT App Inventor format
                hex_color = layout['background_color'].replace('#', '')
                ai_color = f"&H{hex_color.upper()}"
                project_properties["Properties"]["BackgroundColor"] = ai_color
            except:
                pass
        if 'title' in layout:
            project_properties["Properties"]["Title"] = layout['title']
    
    components = []
    
    # Use Gemini-generated components if available
    if gemini_data and 'components' in gemini_data:
        for i, comp in enumerate(gemini_data['components']):
            try:
                component = {
                    "$Name": comp.get('name', f"Component{i+1}"),
                    "$Type": comp.get('type', 'Button'),
                    "$Version": "7",
                    "Uuid": str(uuid.uuid4())
                }
                
                # Add properties from Gemini
                if 'properties' in comp:
                    for prop, value in comp['properties'].items():
                        if prop.startswith('&H') or prop.startswith('#'):
                            # Handle color conversion
                            try:
                                if value.startswith('#'):
                                    hex_color = value.replace('#', '')
                                    component[prop] = f"&H{hex_color.upper()}"
                                else:
                                    component[prop] = value
                            except:
                                component[prop] = value
                        else:
                            component[prop] = value
                
                # Set default properties if not provided
                if 'Width' not in component:
                    component['Width'] = "-2"
                if 'Height' not in component:
                    component['Height'] = "-2"
                    
                components.append(component)
            except Exception as e:
                # Skip malformed components
                continue
    
    # Fallback to basic components if Gemini didn't provide any or they failed
    if not components:
        components = create_fallback_components(app_type, prompt)
    
    # Add components to project
    if components:
        project_properties["Properties"]["$Components"] = components
    
    return project_properties

def create_fallback_components(app_type, prompt):
    """Create fallback components when Gemini fails"""
    components = []
    prompt_lower = prompt.lower()
    
    if 'calculator' in prompt_lower or app_type == 'calculator':
        # Calculator components
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
        
        # Number buttons
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
    else:
        # Basic components
        components.append({
            "$Name": "Button1",
            "$Type": "Button",
            "$Version": "7",
            "BackgroundColor": "&HFF007AFF",
            "FontBold": "True",
            "FontSize": "14",
            "Shape": "1",
            "Text": "Click Me",
            "TextColor": "&HFFFFFFFF",
            "Width": "-2",
            "Height": "-2",
            "Uuid": str(uuid.uuid4())
        })
        
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
    
    return components

def create_blocks_file(app_name, components, gemini_data=None):
    """Create blocks file with potential AI-generated logic"""
    blocks_data = {
        "YaVersion": "208",
        "Source": "Form",
        "Properties": {
            "$Name": "Screen1",
            "$Type": "Form", 
            "$Version": "31"
        }
    }
    
    # Create basic blocks structure
    blocks_data["blocks"] = {
        "languageVersion": 0,
        "blocks": []
    }
    
    # Add basic blocks if Gemini provided block suggestions
    if gemini_data and 'blocks' in gemini_data:
        # For now, keep it simple - MIT App Inventor blocks are complex to generate
        pass
    
    return blocks_data

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/test_gemini', methods=['POST'])
def test_gemini():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data received'})
            
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'No API key provided'})
        
        if not api_key.strip():
            return jsonify({'success': False, 'error': 'Empty API key provided'})
        
        # Test API with a simple request
        print(f"Testing API with key: {api_key[:10]}...")  # Log first 10 chars for debugging
        test_result = call_gemini_api(api_key, "Say hello")
        
        print(f"API test result: {test_result}")  # Debug log
        
        if 'error' in test_result:
            return jsonify({'success': False, 'error': test_result['error']})
        else:
            return jsonify({'success': True, 'message': 'API connection successful', 'response': test_result})
            
    except Exception as e:
        print(f"Exception in test_gemini: {str(e)}")  # Debug log
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'})

@app.route('/save_gemini_key', methods=['POST'])
def save_gemini_key():
    try:
        data = request.json
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'No API key provided'})
        
        # Save API key in session (in production, use proper encryption)
        session['gemini_api_key'] = api_key
        
        return jsonify({'success': True, 'message': 'API key saved successfully'})
        
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
        
        gemini_data = None
        
        # Use Gemini AI if enabled and API key is available
        if use_gemini and 'gemini_api_key' in session:
            try:
                gemini_data = call_gemini_api(session['gemini_api_key'], prompt)
                if 'error' in gemini_data:
                    # Return error details for debugging
                    return jsonify({
                        'error': f"Gemini AI Error: {gemini_data['error']}",
                        'details': 'AI enhancement failed, falling back to basic generation.'
                    }), 200  # Return 200 so frontend can handle gracefully
            except Exception as e:
                # Continue without Gemini if it fails
                gemini_data = None
        
        # Create project structure
        project_data = create_advanced_project_structure(app_name, app_type, prompt, gemini_data)
        components = project_data["Properties"].get("$Components", [])
        
        # Create blocks data
        blocks_data = create_blocks_file(app_name, components, gemini_data)
        
        # Create AIA file in memory
        aia_buffer = io.BytesIO()
        
        # Clean app name for file paths
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
sizing=Responsive
showlistsasjson=true"""
            aia_file.writestr('youngandroidproject/project.properties', project_properties_content)
            
            # Add Screen1.scm
            project_json = json.dumps(project_data, indent=2)
            screen_scm = f'#|\n$JSON\n{project_json}\n|#'
            aia_file.writestr(f'src/appinventor/ai_user/{clean_app_name}/Screen1.scm', screen_scm)
            
            # Add Screen1.bky
            blocks_json = json.dumps(blocks_data, indent=2)
            blocks_content = f'#|\n$JSON\n{blocks_json}\n|#'
            aia_file.writestr(f'src/appinventor/ai_user/{clean_app_name}/Screen1.bky', blocks_content)
            
            # Add required directories
            aia_file.writestr('assets/.gitkeep', '')
            aia_file.writestr('build/.gitkeep', '')
            
            # Add META-INF
            aia_file.writestr('META-INF/MANIFEST.MF', 'Manifest-Version: 1.0\n')
        
        aia_buffer.seek(0)
        
        return send_file(
            aia_buffer,
            as_attachment=True,
            download_name=f'{app_name.replace(" ", "_")}.aia',
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({
            'error': f'Generation failed: {str(e)}',
            'details': 'Please check your inputs and try again. If using Gemini AI, verify your API key is valid.'
        }), 500

if __name__ == '__main__':
    print("🚀 Starting MIT App Inventor AIA Generator with Gemini AI...")
    print("📱 Server running at: http://0.0.0.0:5000")
    print("💡 Navigate to the URL above to start creating AIA files with AI!")
    app.run(host='0.0.0.0', port=5000, debug=True)
