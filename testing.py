from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import math

app = Flask(__name__, static_url_path='/static')
app.debug = True
df = pd.read_csv('BERSIH.csv')

@app.route('/')
def home():
    return render_template('beranda.html')

@app.route('/input', methods=['GET', 'POST'])
def input():
    return render_template('input.html')

@app.route('/cek')
def cek():
    return render_template('cek.html')

@app.route('/normal')
def normal():
    return render_template('normal.html')

@app.route('/oily')
def oily():
    return render_template('oily.html')

@app.route('/combination')
def combination():
    return render_template('combination.html')

@app.route('/dry')
def dry():
    return render_template('dry.html')

@app.route('/filter_products', methods=['POST'])
def filter_products():
    user_label = request.form.get('userLabel').lower()
    user_skintype = request.form.get('userSkinType').lower()
    user_allergens = request.form.getlist('userAllergen')

    df['SkinType'] = df['SkinType'].str.lower()
    df['Label'] = df['Label'].str.lower()
    filtered_df = df[(df['SkinType'] == user_skintype) & (df['Label'] == user_label) & (df["Rank"] > 0)].copy()
    bobot = {'Label': 0.1, 'SkinType': 0.1, 'Harga': 0.5, "Rank": 2}  # Adjusted weights

    for allergen in user_allergens:
        filtered_df = filtered_df[~filtered_df['IngredientsList'].str.lower().str.contains(allergen.lower())]

        if not filtered_df.empty:
            def format_harga(harga):
                return f'Rp{harga:,.0f}'.replace(',', '.')

            normalized_df = filtered_df.copy()
        
            normalized_df['Harga'] = (normalized_df['Harga'] - normalized_df['Harga'].min()) / (normalized_df['Harga'].max() - normalized_df['Harga'].min())
            normalized_df['Rank'] = (normalized_df['Rank'] - normalized_df['Rank'].min()) / (normalized_df['Rank'].max() - normalized_df['Rank'].min())

            ideal_positif = normalized_df.max()
            ideal_negatif = normalized_df.min()
            jarak_positif = (normalized_df[['Harga', 'Rank']] - ideal_positif[['Harga', 'Rank']]) ** 2
            jarak_negatif = (normalized_df[['Harga', 'Rank']] - ideal_negatif[['Harga', 'Rank']]) ** 2
            nilai_kedekatan = np.sqrt((jarak_negatif.sum(axis=1) / (jarak_positif + jarak_negatif).sum(axis=1)).astype(np.float64)).tolist()

            filtered_df['NilaiKedekatan'] = nilai_kedekatan
            sorted_products = filtered_df.sort_values(by=['NilaiKedekatan', 'Harga', 'Rank'], ascending=[True, True, True])

            safe_products = []
            for index, produk in sorted_products.iterrows():
                safe_products.append({
                    'Brand': produk['Brand'],
                    'Name': produk['Name'],
                    'Rank': produk['Rank'],
                    'Price': format_harga(produk['Harga'])
                })

            recommended_product_info = {
                'Brand': sorted_products.iloc[0]['Brand'],
                'Name': sorted_products.iloc[0]['Name'],
                'Rank': sorted_products.iloc[0]['Rank'],
                'Price': format_harga(sorted_products.iloc[0]['Harga'])
            }

            return render_template('result.html', recommended_product_info=recommended_product_info, safe_products=safe_products)

    message = "Tidak ada produk yang sesuai dengan kriteria Anda."
    return render_template('result.html', message=message)
if __name__ == '__main__':
    app.run(debug=True)