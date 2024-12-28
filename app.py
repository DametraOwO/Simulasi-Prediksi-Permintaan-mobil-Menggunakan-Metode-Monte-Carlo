import json
import os
import numpy as np
import math
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Fungsi untuk membaca data dari file JSON
def load_data():
    if os.path.exists('data.json'):
        with open('data.json', 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []  # Jika JSON rusak, kembalikan list kosong
    return []  # Jika file tidak ada, kembalikan list kosong

# Fungsi untuk menyimpan data ke file JSON
def save_data(data):
    with open('data.json', 'w') as file:
        json.dump(data, file, indent=4)

# Fungsi untuk menghitung probabilitas dengan pembulatan
def calculate_probabilities(frequencies):
    total_frequencies = sum(frequencies)
    probabilities = []
    
    for freq in frequencies:
        prob = freq / total_frequencies
        prob_rounded = round(prob * 1000) / 1000  # Pembulatan ke tiga angka di belakang koma
        probabilities.append(prob_rounded)

    return probabilities

# Fungsi untuk menghitung kumulatif dan interval
def calculate_cumulative_intervals(probabilities):
    cumulative = [round(k, 3) for k in np.cumsum(probabilities)]
    intervals = []
    start = 0

    for prob in probabilities:
        end = math.floor(start + (prob * 1000) - 1)
        intervals.append((start, end))
        start = end + 1

    return cumulative, intervals

# Fungsi untuk menghasilkan bilangan acak dan perhitungan terkait
def generate_random_numbers(frequencies, a=32, c=25, m=99, seed=78):
    random_numbers = []
    aZi_plus_c = []
    mod_m = []
    three_digit = []

    Z = seed
    for _ in frequencies:
        Z_next = (a * Z + c) % m

        # Menyimpan hanya hasil perhitungan (tanpa persamaan lengkap)
        aZi_plus_c.append(a * Z + c)
        mod_m.append(Z_next)

        # Menghasilkan angka 3 digit dengan mengalikan jika kurang dari 100
        three_digit_number = Z_next if Z_next >= 100 else Z_next * 10 if Z_next >= 10 else Z_next * 100
        three_digit.append(three_digit_number)

        random_numbers.append(three_digit_number)
        Z = Z_next

    return random_numbers, aZi_plus_c, mod_m, three_digit

# Fungsi utama untuk simulasi
def simulate_probabilitas(frequencies, a=32, c=25, m=99, seed=78):
    probabilities = calculate_probabilities(frequencies)
    cumulative, intervals = calculate_cumulative_intervals(probabilities)
    random_numbers, aZi_plus_c, mod_m, three_digit = generate_random_numbers(frequencies, a, c, m, seed)

    predictions = []
    for number in random_numbers:
        for i, (start, end) in enumerate(intervals):
            if start <= number <= end:
                predictions.append(frequencies[i])
                break

    return probabilities, cumulative, intervals, random_numbers, predictions, aZi_plus_c, mod_m, three_digit

@app.context_processor
def utility_processor():
    return dict(enumerate=enumerate)

@app.route('/')
def index():
    data = load_data()
    return render_template('index.html', data=data)

@app.route('/data_produk')
def data_produk():
    data = load_data()
    return render_template('DataProduk.html', data=data)

@app.route('/simulasi', methods=['GET', 'POST'])
def simulasi():
    if request.method == 'POST':
        jumlah_kategori = int(request.form['jumlah_kategori'])
        permintaan = []
        frekuensi = []

        # Mengambil input nilai a, seed, c, dan m
        a = int(request.form['a'])
        seed = int(request.form['seed'])
        c = int(request.form['c'])
        m = int(request.form['m'])

        for i in range(jumlah_kategori):
            permintaan_item = request.form[f'kategori_{i}_nama']
            frekuensi_item = int(request.form[f'kategori_{i}_frekuensi'])
            permintaan.append(permintaan_item)
            frekuensi.append(frekuensi_item)

        # Simulasi
        probabilitas, kumulatif, interval, bilangan_acak, prediksi, aZi_plus_c, mod_m, tiga_digit = simulate_probabilitas(
            frekuensi, a=a, c=c, m=m, seed=seed
        )

        # Simpan hasil simulasi dalam file JSON
        hasil_simulasi = []
        data_terdahulu = load_data()
        new_id = len(data_terdahulu) + 1

        for i in range(len(permintaan)):
            hasil_simulasi.append({
                'id': new_id,
                'permintaan': permintaan[i],
                'frekuensi': frekuensi[i],
                'probabilitas': probabilitas[i],
                'kumulatif': kumulatif[i],
                'interval': f"{interval[i][0]} - {interval[i][1]}",
                'bilangan_acak': bilangan_acak[i],
                'prediksi': prediksi[i],
                'aZi_plus_c': aZi_plus_c[i],
                'mod_m': mod_m[i],
                'angka_3_digit': tiga_digit[i]
            })
            new_id += 1

        data_terdahulu.extend(hasil_simulasi)
        save_data(data_terdahulu)

        # Hitung rata-rata prediksi
        total_prediksi = sum(item['prediksi'] for item in data_terdahulu)
        jumlah_data = len(data_terdahulu)
        rata_rata_prediksi = total_prediksi // jumlah_data if jumlah_data > 0 else 0

        return render_template('HasilPrediksi.html', hasil_simulasi=data_terdahulu, rata_rata_prediksi=rata_rata_prediksi)

    return render_template('Simulasi.html')

@app.route('/hasil_prediksi')
def hasil_prediksi():
    hasil_simulasi = load_data()
    total_prediksi = sum(item['prediksi'] for item in hasil_simulasi)
    jumlah_data = len(hasil_simulasi)
    rata_rata_prediksi = total_prediksi // jumlah_data if jumlah_data > 0 else 0  # Hindari pembagian nol
    return render_template(
        'HasilPrediksi.html', 
        hasil_simulasi=hasil_simulasi, 
        rata_rata_prediksi=rata_rata_prediksi
    )

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    data = load_data()
    data = [item for item in data if item.get('id') != id]

    for index, item in enumerate(data, start=1):
        item["id"] = index

    save_data(data)
    return redirect(url_for('hasil_prediksi'))

if __name__ == '__main__':
    app.run(debug=True)
