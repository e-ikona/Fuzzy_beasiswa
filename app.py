from flask import Flask, render_template, request
from itertools import product
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

app = Flask(__name__)

fuzzy_config = {
    'ipk_domains': {
        'rendah': [3.0, 3.50],
        'sedang': [3.25, 3.75],
        'tinggi': [3.5, 4.0]
    },
    'pot_domains': {
        'rendah': [0, 3500000],
        'sedang': [1750000, 5250000],
        'tinggi': [3500000, 7000000]
    },
    'jto_domains': {
        'rendah': [1, 3],
        'sedang': [2, 4],
        'tinggi': [3, 5]
    },
    'rules': {
        ('RENDAH', 'RENDAH', 'RENDAH'): 0,
        ('RENDAH', 'RENDAH', 'SEDANG'): 0,
        ('RENDAH', 'SEDANG', 'TINGGI'): 1,
        ('RENDAH', 'SEDANG', 'RENDAH'): 0,
        ('RENDAH', 'SEDANG', 'SEDANG'): 0,
        ('RENDAH', 'SEDANG', 'TINGGI'): 0,
        ('RENDAH', 'TINGGI', 'RENDAH'): 0,
        ('RENDAH', 'TINGGI', 'SEDANG'): 0,
        ('RENDAH', 'TINGGI', 'TINGGI'): 0,
        ('SEDANG', 'RENDAH', 'RENDAH'): 1,
        ('SEDANG', 'RENDAH', 'SEDANG'): 1,
        ('SEDANG', 'RENDAH', 'TINGGI'): 1,
        ('SEDANG', 'SEDANG', 'RENDAH'): 0,
        ('SEDANG', 'SEDANG', 'SEDANG'): 1,
        ('SEDANG', 'SEDANG', 'TINGGI'): 1,
        ('SEDANG', 'TINGGI', 'RENDAH'): 0,
        ('SEDANG', 'TINGGI', 'SEDANG'): 0,
        ('SEDANG', 'TINGGI', 'TINGGI'): 1,
        ('TINGGI', 'RENDAH', 'RENDAH'): 1,
        ('TINGGI', 'RENDAH', 'SEDANG'): 1,
        ('TINGGI', 'RENDAH', 'TINGGI'): 1,
        ('TINGGI', 'SEDANG', 'RENDAH'): 1,
        ('TINGGI', 'SEDANG', 'SEDANG'): 1,
        ('TINGGI', 'SEDANG', 'TINGGI'): 1,
        ('TINGGI', 'TINGGI', 'RENDAH'): 0,
        ('TINGGI', 'TINGGI', 'SEDANG'): 0,
        ('TINGGI', 'TINGGI', 'TINGGI'): 1
    }
}

def fuzzy_ipk(ipk):
    domains = fuzzy_config['ipk_domains']
    if ipk <= domains['rendah'][1]:
        return 'RENDAH', max(0, min((domains['sedang'][1] - ipk) / (domains['sedang'][1] - domains['rendah'][1]), 1))
    elif domains['sedang'][0] < ipk <= domains['sedang'][1]:
        return 'SEDANG', max(0, min((ipk - domains['sedang'][0]) / (domains['sedang'][1] - domains['sedang'][0]), 1))
    elif ipk > domains['tinggi'][0]:
        return 'TINGGI', max(0, min((ipk - domains['tinggi'][0]) / (domains['tinggi'][1] - domains['tinggi'][0]), 1))

def fuzzy_pot(pot):
    domains = fuzzy_config['pot_domains']
    if pot <= domains['rendah'][1]:
        return 'RENDAH', max(0, min((domains['sedang'][1] - pot) / (domains['sedang'][1] - domains['rendah'][0]), 1))
    elif domains['sedang'][0] < pot <= domains['sedang'][1]:
        return 'SEDANG', max(0, min((pot - domains['sedang'][0]) / (domains['sedang'][1] - domains['sedang'][0]), 1))
    elif pot > domains['tinggi'][0]:
        return 'TINGGI', max(0, min((pot - domains['tinggi'][0]) / (domains['tinggi'][1] - domains['tinggi'][0]), 1))

def fuzzy_jto(jto):
    domains = fuzzy_config['jto_domains']
    if jto <= domains['rendah'][1]:
        return 'RENDAH', max(0, min((domains['sedang'][1] - jto) / (domains['sedang'][1] - domains['rendah'][0]), 1))
    elif domains['sedang'][0] < jto <= domains['sedang'][1]:
        return 'SEDANG', max(0, min((jto - domains['sedang'][0]) / (domains['sedang'][1] - domains['sedang'][0]), 1))
    elif jto > domains['tinggi'][0]:
        return 'TINGGI', max(0, min((jto - domains['tinggi'][0]) / (domains['tinggi'][1] - domains['tinggi'][0]), 1))

def fuzzy_evaluation(ipk, pot, jto):
    ipk_f, ipk_mu = fuzzy_ipk(ipk)
    pot_f, pot_mu = fuzzy_pot(pot)
    jto_f, jto_mu = fuzzy_jto(jto)

    rules = fuzzy_config['rules']
    key = (ipk_f, pot_f, jto_f)
    output = rules.get(key, 0)

    mu = min(ipk_mu, pot_mu, jto_mu)
    weighted_output = mu * output

    return 'DITERIMA' if weighted_output >= 0.5 else 'DITOLAK'

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        ipk = float(request.form['ipk'])
        pot = float(request.form['pot'].replace('.', ''))
        jto = int(request.form['jto'])
        result = fuzzy_evaluation(ipk, pot, jto)
    return render_template('index.html', result=result)

@app.route('/update_rules', methods=['GET', 'POST'])
def update_rules():
    message = None
    if request.method == 'POST':
        fuzzy_config['ipk_domains'] = {
            'rendah': [float(request.form['ipk_rendah_min']), float(request.form['ipk_rendah_max'])],
            'sedang': [float(request.form['ipk_sedang_min']), float(request.form['ipk_sedang_max'])],
            'tinggi': [float(request.form['ipk_tinggi_min']), float(request.form['ipk_tinggi_max'])]
        }
        fuzzy_config['pot_domains'] = {
            'rendah': [float(request.form['pot_rendah_min']), float(request.form['pot_rendah_max'])],
            'sedang': [float(request.form['pot_sedang_min']), float(request.form['pot_sedang_max'])],
            'tinggi': [float(request.form['pot_tinggi_min']), float(request.form['pot_tinggi_max'])]
        }
        fuzzy_config['jto_domains'] = {
            'rendah': [float(request.form['jto_rendah_min']), float(request.form['jto_rendah_max'])],
            'sedang': [float(request.form['jto_sedang_min']), float(request.form['jto_sedang_max'])],
            'tinggi': [float(request.form['jto_tinggi_min']), float(request.form['jto_tinggi_max'])]
        }
        for key in fuzzy_config['rules']:
            form_key = f"rule_{'_'.join(key).lower()}"
            fuzzy_config['rules'][key] = int(request.form[form_key])
        message = "Rules and domains updated successfully!"
    return render_template('update_rules.html', fuzzy_config=fuzzy_config, message=message)

@app.route('/membership_graphs')
def membership_graphs():
    plot_filenames = {}
    for var_name, domains in [
        ('ipk', fuzzy_config['ipk_domains']),
        ('pot', fuzzy_config['pot_domains']),
        ('jto', fuzzy_config['jto_domains'])
    ]:
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
    
    if var_name == 'ipk':
        for i, val in enumerate(x):
            _, mu = fuzzy_ipk(val)
            label, _ = fuzzy_ipk(val)
            if label == 'RENDAH':
                rendah[i] = mu
            elif label == 'SEDANG':
                sedang[i] = mu
            elif label == 'TINGGI':
                tinggi[i] = mu
    elif var_name == 'pot':
        for i, val in enumerate(x):
            _, mu = fuzzy_pot(val)
            label, _ = fuzzy_pot(val)
            if label == 'RENDAH':
                rendah[i] = mu
            elif label == 'SEDANG':
                sedang[i] = mu
            elif label == 'TINGGI':
                tinggi[i] = mu
    elif var_name == 'jto':
        for i, val in enumerate(x):
            _, mu = fuzzy_jto(val)
            label, _ = fuzzy_jto(val)
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