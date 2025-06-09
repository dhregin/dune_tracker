from flask import Flask, render_template_string, request, redirect
import json
import os
import boto3
from botocore.exceptions import ClientError
DATA_FILE = "projects.json"
S3_BUCKET = os.environ.get("S3_BUCKET_NAME", "")
S3_KEY = "projects.json"
USE_S3 = os.environ.get("USE_S3", "true").lower() == "true"


s3_client = boto3.client("s3")

app = Flask(__name__)

DATA_FILE = "projects.json"

# === Default Project Data (Base Sustainability) ===
def get_base_sustainability():
    return {
        "steel_ingot": {"needed": 774, "have": 0},
        "cobalt_paste": {"needed": 130, "have": 0},
        "silicone_block": {"needed": 228, "have": 0},
        "plant_fiber": {"needed": 840, "have": 0},
        "fuel_cell": {"needed": 336, "have": 0},
        "water": {"needed": 70602, "have": 0},
        "carbon_ore": {"needed": 3096, "have": 0},
        "iron_ingot": {"needed": 774, "have": 0},
        "iron_ore": {"needed": 3870, "have": 0},
        "flour_sand": {"needed": 1140, "have": 0},
        "erythrite_crystal": {"needed": 390, "have": 0}
    }

def load_projects():
    if USE_S3:
        try:
            obj = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
            return json.loads(obj['Body'].read())
        except ClientError as e:
            print("S3 read error:", e)
            return {"Base Sustainability": get_base_sustainability()}
    else:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        return {"Base Sustainability": get_base_sustainability()}

def save_projects(projects):
    if USE_S3:
        try:
            s3_client.put_object(Bucket=S3_BUCKET, Key=S3_KEY, Body=json.dumps(projects, indent=2))
        except ClientError as e:
            print("S3 write error:", e)
    else:
        with open(DATA_FILE, "w") as f:
            json.dump(projects, f, indent=2)

@app.route("/", methods=["GET", "POST"])
def index():
    projects = load_projects()
    selected = request.args.get("project", "Base Sustainability")

    # --- Handle Deletion of a project ---
    delete_project = request.args.get("delete_project")
    if delete_project and delete_project in projects and delete_project != "Base Sustainability":
        projects.pop(delete_project)
        save_projects(projects)
        return redirect("/")

    # --- Handle Forms ---
    if request.method == "POST":
        # Create new project
        if "new_project" in request.form:
            new_name = request.form.get("new_project", "").strip()
            if new_name and new_name not in projects:
                projects[new_name] = {}
                save_projects(projects)
            return redirect(f"/?project={new_name}" if new_name else "/")

        # Add new item
        elif "add_item" in request.form:
            item = request.form.get("item", "").strip()
            needed = request.form.get("needed", "").strip()
            if item and needed.isdigit():
                projects[selected][item] = {"needed": int(needed), "have": 0}
                save_projects(projects)
            return redirect(f"/?project={selected}")

        # Delete item from project
        elif "delete_item" in request.form:
            del_key = request.form.get("delete_item")
            if del_key in projects[selected]:
                del projects[selected][del_key]
                save_projects(projects)
            return redirect(f"/?project={selected}")

        # Save updated resource counts
        else:
            for item in projects[selected]:
                try:
                    projects[selected][item]["have"] = int(request.form.get(item, 0))
                    projects[selected][item]["needed"] = int(request.form.get(f"needed_{item}", projects[selected][item]["needed"]))
                except:
                    pass

    # --- Build UI ---
    table_rows = ""
    for item in sorted(projects[selected]):
        need = projects[selected][item]["needed"]
        have = projects[selected][item]["have"]
        left = max(need - have, 0)
        table_rows += f"""
        <tr class='resource-row' data-name='{item}'>
            <td>{item}</td>
            <td><input type='number' class='resource-input needed-input' data-type='needed' name='needed_{item}' value='{need}' /></td>
            <td><input type='number' class='resource-input have-input' data-type='have' name='{item}' value='{have}' /></td>
            <td id='resource-display-{item}'>{left}</td>
            <td><button name='delete_item' value='{item}'>❌</button></td>
        </tr>"""

    project_tabs = ""
    for p in projects:
        is_selected = (p == selected)
        project_tabs += f"<span style='margin-right:10px;'>"
        project_tabs += f"<a href='/?project={p}' style='color:{'#fff' if is_selected else '#aaa'};'>{p}</a>"
        if p != "Base Sustainability":
            project_tabs += f" <a href='/?delete_project={p}' style='color:red;'>❌</a>"
        project_tabs += "</span>"

    return render_template_string(f"""
<html>
<head>
    <title>Dune Tracker</title>
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
        input[type='number'], input[type='text'] {{
            background-color: #2c2c2c;
            color: #e0e0e0;
            border: 1px solid #444;
        }}
        input[type='submit'], button {{
            background-color: #444;
            color: #fff;
            padding: 6px 12px;
            border: none;
            cursor: pointer;
        }}
        input[type='submit']:hover, button:hover {{
            background-color: #666;
        }}
        a {{
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <h2>Dune Awakening Crafting Tracker</h2>
    <div style="margin-bottom: 20px;">
        {project_tabs}
    </div>
    <form method="POST">
        <table>
            <tr><th>Resource</th><th>Needed</th><th>Have</th><th>Left</th><th>Remove</th></tr>
            {table_rows}
        </table><br/>
        <input type="submit" value="Save Progress"/>
    </form>
    <hr/>
    <form method="POST">
        <input type="text" name="new_project" placeholder="New Project Name"/>
        <input type="submit" value="Create New Project"/>
    </form>

    <script>
        window.addEventListener("DOMContentLoaded", function () {{
            document.querySelectorAll('.resource-input').forEach(input => {{
                input.addEventListener('input', () => {{
                    const row = input.closest('.resource-row');
                    const name = row.getAttribute('data-name');

                    const haveInput = row.querySelector('.have-input');
                    const neededInput = row.querySelector('.needed-input');

                    const have = parseInt(haveInput.value) || 0;
                    const needed = parseInt(neededInput.value) || 0;

                    const display = document.querySelector(`#resource-display-${{name}}`);
                    if (display) display.textContent = Math.max(needed - have, 0);
                }});
            }});
        }});
    </script>
</body>
</html>
""")

if __name__ == "__main__":
    app.run(debug=True)
