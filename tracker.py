from flask import Flask, render_template_string, request, redirect
import json
import os
from collections import defaultdict

app = Flask(__name__)

# === Core Data Setup ===

wind_turbine_count = 2
wind_trap_count = 2
filter_count = 168
lubricant_count = 168

req = defaultdict(int)
req['steel_ingot'] += 45 * wind_turbine_count + 90 * wind_trap_count + 3 * filter_count
req['cobalt_paste'] += 65 * wind_turbine_count
req['silicone_block'] += 30 * wind_trap_count + 1 * lubricant_count
req['plant_fiber'] += 5 * filter_count
req['fuel_cell'] += 2 * lubricant_count
req['water'] += (60 * filter_count + 4 * lubricant_count)

req['water'] += 50 * req['steel_ingot'] + 25 * req['iron_ingot']
req['carbon_ore'] += 4 * req['steel_ingot']
req['iron_ingot'] += 1 * req['steel_ingot']
req['iron_ore'] += 5 * req['iron_ingot']
req['water'] += 50 * req['silicone_block']
req['flour_sand'] += 5 * req['silicone_block']
req['water'] += 75 * req['cobalt_paste']
req['erythrite_crystal'] += 3 * req['cobalt_paste']

progress_file = "progress.json"
if os.path.exists(progress_file):
    with open(progress_file, "r") as f:
        collected = json.load(f)
else:
    collected = {res: 0 for res in req}

@app.route("/", methods=["GET", "POST"])
def tracker():
    global collected
    if request.method == "POST":
        for res in req:
            val = request.form.get(res)
            try:
                collected[res] = int(val)
            except:
                collected[res] = 0
        with open(progress_file, "w") as f:
            json.dump(collected, f)
        return redirect("/")

    table_rows = ""
    for res in sorted(req):
        need = req[res]
        have = collected.get(res, 0)
        left = max(need - have, 0)
        table_rows += f"""
        <tr>
            <td>{res}</td>
            <td>{need}</td>
            <td><input type='number' name='{res}' value='{have}'/></td>
            <td>{left}</td>
        </tr>"""

    return render_template_string(f"""
<html>
<head>
    <title>Dune Resource Tracker</title>
    <style>
        body {{
            background-color: #1e1e1e;
            color: #e0e0e0;
            font-family: sans-serif;
            padding: 30px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        th, td {{
            border: 1px solid #555;
            padding: 10px;
        }}
        input[type='number'] {{
            background-color: #2c2c2c;
            color: #e0e0e0;
            border: 1px solid #444;
        }}
        input[type='submit'] {{
            background-color: #444;
            color: #fff;
            padding: 10px 20px;
            border: none;
            margin-top: 10px;
            cursor: pointer;
        }}
        input[type='submit']:hover {{
            background-color: #666;
        }}
    </style>
</head>
<body>
    <h2>Dune Awakening Crafting Tracker</h2>
    <form method="POST">
        <table>
            <tr><th>Resource</th><th>Needed</th><th>Have</th><th>Left</th></tr>
            {table_rows}
        </table><br/>
        <input type="submit" value="Save Progress"/>
    </form>
</body>
</html>
""")

if __name__ == "__main__":
    app.run(debug=True)