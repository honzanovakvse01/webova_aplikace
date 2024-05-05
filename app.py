from flask import Flask, render_template, request
import mysql.connector
from mysql.connector import Error
import pandas as pd

app = Flask(__name__)

# Parametry připojení k databázi
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'bp',
    'port': 1111
}

def pripojeni_k_databazi():
    pripojeni = None
    try:
        pripojeni = mysql.connector.connect(**db_config)
    except Error as e:
        print(f"Chyba při připojování k databázi: {e}")
    return pripojeni

@app.template_filter()
def format_mena(value):
    return f"{value:,.0f}".replace(",", " ")

app.jinja_env.filters['format_mena'] = format_mena

def ziskat_razene_byty(stranka, na_stranku, radit_podle, order, flat_type):
    sql = 'SELECT loc, price, predicted, area, type, oblast, img, seoLoc, hash_id FROM flatsSell WHERE predicted > 0 and personal = 1 and collective = 0'
    
    if flat_type != '':
        sql += f" AND type='{flat_type}'"

    pripojeni = pripojeni_k_databazi()
    byty = pd.read_sql(sql, pripojeni)
    pripojeni.close()

    # Určení decilů
    prvni_decil = byty['price'].quantile(0.1)
    posledni_decil = byty['price'].quantile(0.9)

    # Řazené datové sady na základě argumentů a decilů
    razene_byty = byty[(byty['price'] > prvni_decil) & (byty['price'] < posledni_decil)]
    razene_byty = razene_byty.drop_duplicates(subset=["hash_id"])
    razene_byty['navratnost'] = (razene_byty['price'] / razene_byty["predicted"]) / 12
    razene_byty = razene_byty.sort_values(by=radit_podle, ascending=(order=='asc'))

    # Pagination
    zacatek = (stranka - 1) * na_stranku
    konec = stranka * na_stranku
    return razene_byty[zacatek:konec]

@app.route('/')
def home():
    stranka = request.args.get('page', 1, type=int)
    na_stranku = 20

    radit_podle = request.args.get('radit_podle', 'navratnost') 
    poradi = request.args.get('poradi', 'asc')  
    typ_bytu = request.args.get('typ', '')  
    typ_bytu = typ_bytu.replace(' ', '+')

    razene_byty = ziskat_razene_byty(stranka, na_stranku, radit_podle, poradi, typ_bytu)
    
    byty_k_zobrazeni = razene_byty.to_dict('records')

    if stranka - 1 > 0:
        predchozi_stranka = stranka - 1
    else:
        predchozi_stranka = None
    
    dalsi_stranka = stranka + 1

    return render_template('byty.html', byty=byty_k_zobrazeni, stranka=stranka,
                           radit_podle=radit_podle, poradi=poradi, typ_bytu=typ_bytu,
                           predchozi_stranka=predchozi_stranka, dalsi_stranka=dalsi_stranka)


if __name__ == '__main__':
    app.run()

