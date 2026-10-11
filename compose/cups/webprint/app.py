import os
import subprocess
import uuid
import re
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp', 'gif', 'txt', 'csv', 'log', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_printers():
    printers = []
    default_printer = None
    try:
        # Get default printer
        d_out = subprocess.check_output(['lpstat', '-d'], stderr=subprocess.STDOUT, text=True)
        m = re.search(r'system default destination:\s*([^\s]+)', d_out)
        if m:
            default_printer = m.group(1).strip()
    except Exception:
        pass

    try:
        # Get printer statuses
        p_out = subprocess.check_output(['lpstat', '-p'], stderr=subprocess.STDOUT, text=True)
        for line in p_out.splitlines():
            m = re.match(r'printer\s+([^\s]+)\s+is\s+([^\.]+)', line)
            if m:
                p_name = m.group(1).strip()
                p_status = m.group(2).strip()
                printers.append({
                    'name': p_name,
                    'status': p_status,
                    'is_default': (p_name == default_printer)
                })
    except Exception:
        pass

    if not printers:
        printers.append({'name': 'Epson_L3110', 'status': 'ready', 'is_default': True})
    return printers

def get_queue():
    jobs = []
    try:
        q_out = subprocess.check_output(['lpstat', '-o'], stderr=subprocess.STDOUT, text=True)
        for line in q_out.splitlines():
            # Format: Epson_L3110-14 blessen 1024 Mon 31 Aug 2026 11:15:00 PM UTC
            parts = line.split()
            if len(parts) >= 4:
                job_id = parts[0]
                user = parts[1]
                size = parts[2]
                time_str = " ".join(parts[3:])
                jobs.append({
                    'id': job_id,
                    'user': user,
                    'size': size,
                    'time': time_str
                })
    except Exception:
        pass
    return jobs

@app.route('/')
def index():
    printers = get_printers()
    queue = get_queue()
    return render_template('index.html', printers=printers, queue=queue)

@app.route('/api/status')
def api_status():
    return jsonify({
        'printers': get_printers(),
        'queue': get_queue()
    })

@app.route('/api/print', methods=['POST'])
def print_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': f'Unsupported file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    filename = secure_filename(file.filename)
    unique_prefix = uuid.uuid4().hex[:8]
    saved_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_prefix}_{filename}")
    file.save(saved_path)

    # Print options
    printer = request.form.get('printer', 'Epson_L3110')
    copies = request.form.get('copies', '1')
    color_mode = request.form.get('color_mode', 'color') # 'color' or 'mono'
    media = request.form.get('media', 'A4')
    page_ranges = request.form.get('page_ranges', '').strip()
    orientation = request.form.get('orientation', 'portrait')
    fit_to_page = request.form.get('fit_to_page', 'true') == 'true'

    cmd = ['lp', '-d', printer]

    # Copies
    try:
        num_copies = int(copies)
        if num_copies > 0:
            cmd.extend(['-n', str(num_copies)])
    except ValueError:
        pass

    # Media / Paper size
    if media:
        cmd.extend(['-o', f'media={media}'])

    # Color mode
    if color_mode == 'mono':
        cmd.extend(['-o', 'print-color-mode=monochrome', '-o', 'ColorModel=Gray'])
    else:
        cmd.extend(['-o', 'print-color-mode=color', '-o', 'ColorModel=RGB'])

    # Orientation
    if orientation == 'landscape':
        cmd.extend(['-o', 'landscape'])
    elif orientation == 'portrait':
        cmd.extend(['-o', 'portrait'])

    # Page range
    if page_ranges:
        cmd.extend(['-o', f'page-ranges={page_ranges}'])

    # Fit to page
    if fit_to_page:
        cmd.extend(['-o', 'fit-to-page'])

    cmd.append(saved_path)

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        # lp output: "request id is Epson_L3110-15 (1 file(s))"
        job_match = re.search(r'request id is\s+([^\s]+)', output)
        job_id = job_match.group(1) if job_match else "Submitted"
        
        return jsonify({
            'success': True,
            'message': f'Print job submitted successfully! (Job ID: {job_id})',
            'job_id': job_id,
            'details': output.strip()
        })
    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False,
            'error': f'Printing failed: {e.output}'
        }), 500
    except Exception as ex:
        return jsonify({
            'success': False,
            'error': f'System error: {str(ex)}'
        }), 500

@app.route('/api/cancel', methods=['POST'])
def cancel_job():
    data = request.get_json(silent=True) or request.form
    job_id = data.get('job_id')
    if not job_id:
        return jsonify({'success': False, 'error': 'job_id is required'}), 400
    try:
        subprocess.check_output(['cancel', str(job_id)], stderr=subprocess.STDOUT, text=True)
        return jsonify({'success': True, 'message': f'Job {job_id} cancelled.'})
    except subprocess.CalledProcessError as e:
        return jsonify({'success': False, 'error': f'Failed to cancel job: {e.output}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8084, debug=False)
