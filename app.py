from flask import Flask, render_template, request
from itertools import product
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
import json

app = Flask(__name__)

# Path untuk menyimpan konfigurasi
CONFIG_FILE = 'fuzzy_config.json'

# Default konfigurasi
default_config = {
    'variables': {
        'ipk': {
            'rendah': [3.0, 3.50],
            'sedang': [3.25, 3.75],
            'tinggi': [3.5, 4.0]
        },
        'pot': {
            'rendah': [0, 3500000],
            'sedang': [1750000, 5250000],
            'tinggi': [3500000, 7000000]
        },
        'jto': {
            'rendah': [1, 3],
            'sedang': [2, 4],
            'tinggi': [3, 5]
        }
    },
    'rules': {}
}

# Fungsi untuk menghasilkan aturan berdasarkan variabel
def generate_rules(variables):
    levels = ['RENDAH', 'SEDANG', 'TINGGI']
    var_names = list(variables.keys())
    rule_keys = list(product(levels, repeat=len(var_names)))
    rules = {}
    for key in rule_keys:
        rule_key = tuple(key)
        # Default value: 0 (Ditolak)
        rules[rule_key] = 0
    return rules

# Migrasi struktur lama ke struktur baru
def migrate_config(loaded_config):
    if 'variables' in loaded_config:
        # Sudah menggunakan struktur baru, tidak perlu migrasi
        return loaded_config

    # Struktur lama: ipk_domains, pot_domains, jto_domains
    new_config = {'variables': {}, 'rules': {}}
    if 'ipk_domains' in loaded_config:
        new_config['variables']['ipk'] = loaded_config['ipk_domains']
    if 'pot_domains' in loaded_config:
        new_config['variables']['pot'] = loaded_config['pot_domains']
    if 'jto_domains' in loaded_config:
        new_config['variables']['jto'] = loaded_config['jto_domains']

    # Konversi rules
    if 'rules' in loaded_config:
        new_config['rules'] = {
            tuple(k.split('_')): v for k, v in loaded_config['rules'].items()
        }

    # Jika tidak ada variabel, gunakan default
    if not new_config['variables']:
        new_config['variables'] = default_config['variables']

    # Generate ulang rules jika perlu
    if not new_config['rules'] or len(list(new_config['rules'].keys())[0]) != len(new_config['variables']):
        new_config['rules'] = generate_rules(new_config['variables'])

    return new_config

# Muat konfigurasi dari file jika ada, jika tidak gunakan default
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        loaded_config = json.load(f)
    # Migrasi konfigurasi ke struktur baru
    fuzzy_config = migrate_config(loaded_config)
    # Simpan kembali konfigurasi yang sudah dimigrasi
    with open(CONFIG_FILE, 'w') as f:
        config_to_save = fuzzy_config.copy()
        config_to_save['rules'] = {f"{'_'.join(k)}": v for k, v in fuzzy_config['rules'].items()}
        json.dump(config_to_save, f, indent=4)
else:
    fuzzy_config = default_config.copy()
    # Generate rules berdasarkan variabel default
    fuzzy_config['rules'] = generate_rules(fuzzy_config['variables'])
    # Simpan ke JSON dengan kunci sebagai string
    with open(CONFIG_FILE, 'w') as f:
        config_to_save = fuzzy_config.copy()
        config_to_save['rules'] = {f"{'_'.join(k)}": v for k, v in fuzzy_config['rules'].items()}
        json.dump(config_to_save, f, indent=4)

# Fungsi fuzzy untuk setiap variabel
def fuzzy_variable(value, var_name):
    domains = fuzzy_config['variables'][var_name]
    if value <= domains['rendah'][1]:
        return 'RENDAH', max(0, min((domains['sedang'][1] - value) / (domains['sedang'][1] - domains['rendah'][0]), 1))
    elif domains['sedang'][0] < value <= domains['sedang'][1]:
        return 'SEDANG', max(0, min((value - domains['sedang'][0]) / (domains['sedang'][1] - domains['sedang'][0]), 1))
    elif value > domains['tinggi'][0]:
        return 'TINGGI', max(0, min((value - domains['tinggi'][0]) / (domains['tinggi'][1] - domains['tinggi'][0]), 1))
    return None, 0

def fuzzy_evaluation(inputs):
    var_names = list(fuzzy_config['variables'].keys())
    memberships = {}
    for var_name, value in inputs.items():
        label, mu = fuzzy_variable(value, var_name)
        memberships[var_name] = (label, mu)

    rules = fuzzy_config['rules']
    weighted_outputs = []
    for rule_key, output in rules.items():
        mu_values = []
        for i, var_name in enumerate(var_names):
            label, mu = memberships[var_name]
            if label != rule_key[i]:
                mu = 0
            mu_values.append(mu)
        rule_mu = min(mu_values)
        weighted_outputs.append(rule_mu * output)

    final_output = sum(weighted_outputs) / len(weighted_outputs) if weighted_outputs else 0
    return 'DITERIMA' if final_output >= 0.5 else 'DITOLAK'

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        inputs = {}
        for var_name in fuzzy_config['variables'].keys():
            value = request.form[var_name]
            if var_name == 'pot':
                value = float(value.replace('.', ''))
            elif var_name == 'jto':
                value = int(value)
            else:
                value = float(value)
            inputs[var_name] = value
        result = fuzzy_evaluation(inputs)
    return render_template('index.html', result=result, variables=fuzzy_config['variables'])

@app.route('/update_rules', methods=['GET', 'POST'])
def update_rules():
    global fuzzy_config
    message = None
    if request.method == 'POST':
        # Update domains
        for var_name in fuzzy_config['variables'].keys():
            fuzzy_config['variables'][var_name] = {
                'rendah': [float(request.form[f'{var_name}_rendah_min']), float(request.form[f'{var_name}_rendah_max'])],
                'sedang': [float(request.form[f'{var_name}_sedang_min']), float(request.form[f'{var_name}_sedang_max'])],
                'tinggi': [float(request.form[f'{var_name}_tinggi_min']), float(request.form[f'{var_name}_tinggi_max'])]
            }
        for key in fuzzy_config['rules']:
            form_key = f"rule_{'_'.join(key).lower()}"
            fuzzy_config['rules'][key] = int(request.form[form_key])
        with open(CONFIG_FILE, 'w') as f:
            config_to_save = fuzzy_config.copy()
            config_to_save['rules'] = {f"{'_'.join(k)}": v for k, v in fuzzy_config['rules'].items()}
            json.dump(config_to_save, f, indent=4)
        message = "Rules and domains updated successfully!"
    return render_template('update_rules.html', fuzzy_config=fuzzy_config, message=message)

@app.route('/update_variables', methods=['GET', 'POST'])
def update_variables():
    global fuzzy_config
    message = None
    if request.method == 'POST':
        if 'add_variable' in request.form:
            var_name = request.form['var_name'].strip().lower()
            if var_name and var_name not in fuzzy_config['variables']:
                fuzzy_config['variables'][var_name] = {
                    'rendah': [float(request.form[f'var_rendah_min']), float(request.form[f'var_rendah_max'])],
                    'sedang': [float(request.form[f'var_sedang_min']), float(request.form[f'var_sedang_max'])],
                    'tinggi': [float(request.form[f'var_tinggi_min']), float(request.form[f'var_tinggi_max'])]
                }
                # Regenerate rules
                fuzzy_config['rules'] = generate_rules(fuzzy_config['variables'])
                message = f"Variable '{var_name}' added successfully!"
            else:
                message = "Variable name already exists or is invalid."
        elif 'delete_variable' in request.form:
            var_name = request.form['delete_variable']
            if var_name in fuzzy_config['variables']:
                if len(fuzzy_config['variables']) > 1:  
                    del fuzzy_config['variables'][var_name]
                    fuzzy_config['rules'] = generate_rules(fuzzy_config['variables'])
                    message = f"Variable '{var_name}' deleted successfully!"
                else:
                    message = "Cannot delete the last variable. At least one variable must remain."
            else:
                message = "Variable not found."
        
        # Simpan ke file
        with open(CONFIG_FILE, 'w') as f:
            config_to_save = fuzzy_config.copy()
            config_to_save['rules'] = {f"{'_'.join(k)}": v for k, v in fuzzy_config['rules'].items()}
            json.dump(config_to_save, f, indent=4)

    return render_template('update_variables.html', fuzzy_config=fuzzy_config, message=message)

@app.route('/membership_graphs')
def membership_graphs():
    plot_filenames = {}
    for var_name, domains in fuzzy_config['variables'].items():
        plot_filename = generate_membership_plot(var_name, domains)
        plot_filenames[var_name] = plot_filename
    
    return render_template('membership_graphs.html', plot_filenames=plot_filenames)

def generate_membership_plot(var_name, domains):
    min_val = min(domains['rendah'][0], domains['sedang'][0], domains['tinggi'][0]) * 0.8
    max_val = max(domains['rendah'][1], domains['sedang'][1], domains['tinggi'][1]) * 1.2
    x = np.linspace(min_val, max_val, 1000) 
    
    rendah = np.zeros_like(x)
    sedang = np.zeros_like(x)
    tinggi = np.zeros_like(x)
    
    for i, val in enumerate(x):
        label, mu = fuzzy_variable(val, var_name)
        if label == 'RENDAH':
            rendah[i] = mu
        elif label == 'SEDANG':
            sedang[i] = mu
        elif label == 'TINGGI':
            tinggi[i] = mu
    
    plt.figure(figsize=(8, 5))
    plt.plot(x, rendah, label='Rendah', color='blue')
    plt.plot(x, sedang, label='Sedang', color='green')
    plt.plot(x, tinggi, label='Tinggi', color='red')
    plt.title(f'Fungsi Keanggotaan untuk {var_name.upper()}')
    plt.xlabel(var_name.upper())
    plt.ylabel('Derajat Keanggotaan')
    plt.legend()
    plt.grid(True)
    
    static_dir = os.path.join(app.root_path, 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    plot_path = os.path.join(static_dir, f'{var_name}_membership.png')
    plt.savefig(plot_path)
    plt.close()
    
    return f'{var_name}_membership.png'

if __name__ == '__main__':
    app.run(debug=True)