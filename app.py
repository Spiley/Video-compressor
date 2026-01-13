import os
import subprocess
import uuid
from flask import Flask, request, send_file, render_template_string
import static_ffmpeg

# Initialisatie
static_ffmpeg.add_paths()
UPLOAD_FOLDER = 'temp_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video Super Compressor</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding: 20px; background-color: #f4f6f9; color: #333; }
        .container { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }
        
        h1 { margin-bottom: 5px; color: #2c3e50; }
        p.subtitle { color: #7f8c8d; margin-bottom: 25px; font-size: 0.9em; }

        .form-group { margin-bottom: 20px; text-align: left; background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef; }
        label { font-weight: bold; display: block; margin-bottom: 8px; color: #34495e; }
        
        input[type="file"] { width: 100%; padding: 8px; background: white; border: 1px solid #ccc; border-radius: 4px; }
        select { width: 100%; padding: 10px; border-radius: 4px; border: 1px solid #ccc; font-size: 14px; }

        /* Info Box */
        .info-box { display: flex; justify-content: space-between; background: #e8f4fc; padding: 15px; border-radius: 6px; margin-bottom: 20px; border-left: 5px solid #3498db; }
        .info-item { text-align: center; flex: 1; }
        .info-label { font-size: 11px; text-transform: uppercase; color: #555; letter-spacing: 0.5px; }
        .info-value { font-size: 20px; font-weight: bold; color: #2980b9; margin-top: 5px; }

        /* Slider */
        input[type="range"] { -webkit-appearance: none; width: 100%; height: 8px; border-radius: 5px; background: #d3d3d3; outline: none; margin: 20px 0; }
        input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; width: 24px; height: 24px; border-radius: 50%; background: #e74c3c; cursor: pointer; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
        .range-labels { display: flex; justify-content: space-between; font-size: 12px; color: #777; font-weight: bold; }

        button { background-color: #27ae60; color: white; padding: 15px; border: none; border-radius: 6px; cursor: pointer; font-size: 18px; width: 100%; font-weight: bold; transition: background 0.2s; }
        button:hover { background-color: #219150; }
        button:disabled { background-color: #95a5a6; cursor: not-allowed; }

        /* Progress */
        #progress-wrapper { display: none; margin-top: 25px; }
        progress { width: 100%; height: 25px; border-radius: 12px; }
        #status-text { margin-top: 8px; font-weight: bold; color: #555; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Video Super Compressor</h1>
        <p class="subtitle">Slimmer comprimeren op basis van tijd.</p>
        
        <form id="uploadForm">
            <div class="form-group">
                <label>1. Kies bestand:</label>
                <input type="file" name="video" id="videoInput" accept="video/*" required>
                <video id="hiddenVideo" style="display:none;"></video>
            </div>

            <div class="info-box">
                <div class="info-item">
                    <div class="info-label">Origineel</div>
                    <div class="info-value" id="origSize">- MB</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Duur</div>
                    <div class="info-value" id="videoDuration">- min</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Nieuwe Grootte</div>
                    <div class="info-value" id="estSize">- MB</div>
                </div>
            </div>

            <div class="form-group">
                <label>2. Formaat (Resolutie):</label>
                <select name="resolution" id="resInput">
                    <option value="original">Origineel behouden</option>
                    <option value="720">HD Ready (720p)</option>
                    <option value="480" selected>Mobiel (480p) - Kleinste!</option>
                </select>
            </div>

            <div class="form-group">
                <label>3. Kwaliteit vs Grootte:</label>
                <div class="range-labels">
                    <span>Hogere Kwaliteit</span>
                    <span>Kleiner Bestand</span>
                </div>
                <input type="range" min="0" max="100" value="70" id="qualitySlider" name="qualityPercent">
                <div id="bitrateInfo" style="text-align: center; font-size: 13px; color: #e74c3c; font-weight: bold;">
                    ~0.5 MB per minuut video
                </div>
            </div>

            <button type="submit" id="submitBtn">Comprimeer Video</button>
        </form>

        <div id="progress-wrapper">
            <progress id="progressBar" value="0" max="100"></progress>
            <p id="status-text">Wachten op start...</p>
        </div>
    </div>

    <script>
        const videoInput = document.getElementById('videoInput');
        const hiddenVideo = document.getElementById('hiddenVideo');
        const qualitySlider = document.getElementById('qualitySlider');
        const resInput = document.getElementById('resInput');
        
        const origSizeEl = document.getElementById('origSize');
        const estSizeEl = document.getElementById('estSize');
        const durationEl = document.getElementById('videoDuration');
        const bitrateInfo = document.getElementById('bitrateInfo');

        let durationSeconds = 0;

        // Hulpfunctie voor mooie getallen
        function formatBytes(bytes) {
            if (bytes === 0) return '- MB';
            const mb = bytes / (1024 * 1024);
            return mb.toFixed(1) + ' MB';
        }

        // 1. Zodra bestand gekozen is: Laad metadata voor duur
        videoInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                origSizeEl.innerText = formatBytes(file.size);
                
                const fileURL = URL.createObjectURL(file);
                hiddenVideo.src = fileURL;
            }
        });

        // 2. Als metadata geladen is (we weten nu de lengte)
        hiddenVideo.addEventListener('loadedmetadata', function() {
            durationSeconds = hiddenVideo.duration;
            
            // Zet om naar min:sec
            const mins = Math.floor(durationSeconds / 60);
            const secs = Math.floor(durationSeconds % 60);
            durationEl.innerText = `${mins}:${secs.toString().padStart(2, '0')}`;
            
            calculateEstimate();
        });

        // 3. De rekenmachine
        function calculateEstimate() {
            if (durationSeconds === 0) return;

            const sliderVal = parseInt(qualitySlider.value); // 0 tot 100
            const resolution = resInput.value;

            // Basis bitrate aannames in Megabits per seconde (Mbps)
            // Dit zijn realistische waarden voor x264 compressie
            let estimatedBitrate = 0;

            // Stap 1: Bepaal basis bitrate obv resolutie
            if (resolution === '480') {
                estimatedBitrate = 1.0; // Startpunt 1 Mbps
            } else if (resolution === '720') {
                estimatedBitrate = 2.5; // Startpunt 2.5 Mbps
            } else {
                estimatedBitrate = 5.0; // Original
            }

            // Stap 2: Pas aan obv slider (0 = Hoogste kwaliteit, 100 = Hoogste compressie)
            // Bij 100% slider reduceren we de bitrate enorm
            // Factor loopt van 1.2 (hoge kwaliteit) tot 0.2 (extreme compressie)
            const compressionFactor = 1.2 - (sliderVal / 100); 
            
            let finalBitrateMbps = estimatedBitrate * compressionFactor;
            
            // Minimum bewaking (anders wordt het 0)
            if (finalBitrateMbps < 0.1) finalBitrateMbps = 0.1;

            // Stap 3: Berekenen
            // (Bitrate * Seconden) / 8 = MegaBytes
            const estimatedMB = (finalBitrateMbps * durationSeconds) / 8;

            estSizeEl.innerText = "~ " + estimatedMB.toFixed(1) + " MB";
            
            // Update tekst onder slider
            const mbPerMin = (finalBitrateMbps * 60) / 8;
            bitrateInfo.innerText = `~${mbPerMin.toFixed(1)} MB per minuut video`;
        }

        qualitySlider.addEventListener('input', calculateEstimate);
        resInput.addEventListener('change', calculateEstimate);

        // Upload Logica (Dezelfde als voorheen)
        const form = document.getElementById('uploadForm');
        const submitBtn = document.getElementById('submitBtn');
        const progressWrapper = document.getElementById('progress-wrapper');
        const progressBar = document.getElementById('progressBar');
        const statusText = document.getElementById('status-text');

        form.addEventListener('submit', function(e) {
            e.preventDefault();
            if(videoInput.files.length === 0) return;

            const formData = new FormData(form);
            const xhr = new XMLHttpRequest();

            submitBtn.disabled = true;
            submitBtn.innerText = "Bezig met uploaden...";
            progressWrapper.style.display = 'block';

            xhr.upload.addEventListener("progress", function(e) {
                if (e.lengthComputable) {
                    const pct = (e.loaded / e.total) * 100;
                    progressBar.value = pct;
                    statusText.innerText = `Uploaden: ${Math.round(pct)}%`;
                    if(pct >= 100) {
                        statusText.innerText = "Bezig met comprimeren... (Sluit dit venster niet)";
                        progressBar.removeAttribute('value');
                    }
                }
            });

            xhr.onload = function() {
                if (xhr.status === 200) {
                    statusText.innerText = "Klaar! Download start.";
                    const blob = new Blob([xhr.response], { type: "video/mp4" });
                    const link = document.createElement("a");
                    link.href = window.URL.createObjectURL(blob);
                    link.download = "video_klein.mp4";
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    submitBtn.disabled = false;
                    submitBtn.innerText = "Nog een video doen";
                } else {
                    statusText.innerText = "Fout: " + xhr.statusText;
                    submitBtn.disabled = false;
                }
            };
            
            xhr.onerror = function() { statusText.innerText = "Netwerkfout."; submitBtn.disabled = false; };
            xhr.open("POST", "/compress", true);
            xhr.responseType = "blob";
            xhr.send(formData);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/compress', methods=['POST'])
def compress():
    file = request.files['video']
    quality_percent = request.form.get('qualityPercent', '70')
    resolution = request.form.get('resolution', 'original')
    
    if not file: return "Geen bestand", 400

    filename = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, filename + "_in.mp4")
    output_path = os.path.join(UPLOAD_FOLDER, filename + "_out.mp4")
    file.save(input_path)

    # Conversie Slider -> CRF
    # 0 (Links) = CRF 20 (Mooi)
    # 100 (Rechts) = CRF 45 (Blokkerig, heel klein)
    try:
        val = int(quality_percent)
    except:
        val = 70
        
    min_crf = 20
    max_crf = 45
    crf_value = str(int(min_crf + ((val / 100) * (max_crf - min_crf))))

    cmd = ["ffmpeg", "-i", input_path, "-vcodec", "libx264", "-crf", crf_value, "-preset", "veryfast"]

    # Resolutie instellingen
    if resolution == "720":
        cmd.extend(["-vf", "scale=-2:720"])
    elif resolution == "480":
        cmd.extend(["-vf", "scale=-2:480"])
    
    # Audio compressie (mono geluid voor mobiel bespaart veel, anders stereo)
    if val > 80: # Bij extreme compressie
        cmd.extend(["-ac", "1", "-b:a", "64k"]) # Mono, lage bitrate
    else:
        cmd.extend(["-b:a", "128k"]) # Standaard

    cmd.append(output_path)

    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        return f"Fout: {str(e)}", 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

    try:
        return send_file(output_path, as_attachment=True, download_name="video_klein.mp4")
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    print("Website draait op http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000)